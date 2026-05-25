import shutil
import tempfile
import httpx
import structlog
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from vs_analyst import get_logger, settings
from vs_analyst.utility.storage.s3 import S3StorageProvider
from vs_analyst.orchestrator.pipeline import run_pipeline
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.schemas.user_inputs import UserInputSchema, InvestmentStage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


logger = get_logger(__name__)

class AnalysisRequest(BaseModel):
    file_path: str = Field(..., description="MinIO file key or path for the pitch deck")
    startup_name: str = Field(..., description="Name of the startup")
    industry_sector: str = Field(..., description="E.g., SaaS, AI, HealthTech")
    funding_stage: Optional[str] = Field(default=None, description="E.g., pre-seed, seed, series_a")
    requested_amount: float = Field(..., description="Amount raising")
    run_id: str | None = Field(default=None, description="Optional distributed tracing correlation ID passed from backend")


class AnalysisService:
    def __init__(self):
        self.storage = S3StorageProvider()
        # Retrieve optional callback URL from config
        self.callback_url = settings.backend_callback_url

    async def send_webhook(
        self,
        run_id: str,
        event_type: str,
        status: str,
        message: str,
        data: Optional[dict] = None
    ) -> None:
        """
        Sends an asynchronous HTTP POST webhook update to the backend callback endpoint.
        
        Args:
            run_id: Correlation ID for the pipeline execution.
            event_type: Name of the pipeline event (e.g. 'pipeline_start', 'pipeline_success').
            status: Progress status (e.g. 'processing', 'completed', 'failed').
            message: Human-readable update description.
            data: Optional dictionary containing additional outputs (e.g. final report).
        """
        if not self.callback_url:
            logger.debug("No callback URL configured. Skipping webhook notify.", run_id=run_id)
            return

        payload = {
            "run_id": run_id,
            "event": event_type,
            "status": status,
            "message": message,
            "data": data or {}
        }

        logger.info(
            "Sending webhook update to backend",
            run_id=run_id,
            event=event_type,
            status=status,
            callback_url=str(self.callback_url)
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(str(self.callback_url), json=payload, timeout=8.0)
                response.raise_for_status()
                logger.debug("Webhook update acknowledged by backend", run_id=run_id, status_code=response.status_code)
        except Exception as e:
            logger.error(
                "Failed to send webhook update to backend",
                run_id=run_id,
                error=str(e),
                callback_url=str(self.callback_url)
            )

    async def execute_analysis(
        self,
        run_id: str,
        file_path: str,
        startup_name: str,
        industry_sector: str,
        funding_stage: Optional[str],
        requested_amount: float
    ) -> None:
        """
        Orchestrates the entire asynchronous pipeline process:
          1. Creates an isolated sandbox folder.
          2. Downloads the target pitch deck from storage.
          3. Normalizes input arguments.
          4. Executes the LangGraph multi-agent analysis pipeline.
          5. Generates the structured summary report.
          6. Dispatches webhook events to the backend at startup, major phases, and completion/failure.
          7. Cleans up the sandbox directory in a finally block to maintain 100% stateless execution.
        """
        # Define isolated local sandbox directory inside standard temp workspace
        temp_base = Path(tempfile.gettempdir()) / "vc_analyst_runs"
        sandbox_dir = temp_base / f"run_{run_id}"

        # Initialize tracing variable inside structlog's contextvars
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(run_id=run_id)

        logger.info("Initializing isolated analysis session", sandbox=str(sandbox_dir))
        
        # 1. Prepare Sandbox
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        await self.send_webhook(
            run_id,
            event_type="pipeline_start",
            status="processing",
            message="Workspace prepared. Preparing file download..."
        )

        try:
            # 2. Download File using S3 Provider
            file_ext = Path(file_path).suffix.lower()
            local_deck_path = sandbox_dir / f"deck{file_ext}"

            logger.info("Fetching deck from storage", key=file_path, target=str(local_deck_path))
            self.storage.download_file(file_path, local_deck_path)
            
            await self.send_webhook(
                run_id,
                event_type="file_downloaded",
                status="processing",
                message="Pitch deck downloaded successfully. Running multi-agent VC analysis..."
            )

            # 3. Normalize and strictly validate Investment Stage string to Enum
            try:
                stage_enum = InvestmentStage.from_str(funding_stage)
            except ValueError as e:
                logger.error("Strict investment stage validation failed", provided_stage=funding_stage, error=str(e))
                raise e

            # 4. Construct Schemas and Pipeline State
            user_input = UserInputSchema(
                pitch_deck_path=local_deck_path,
                investment_stage=stage_enum,
                website_url=f"https://{startup_name.lower().replace(' ', '')}.com",
                sector=industry_sector,
                ask_amount=requested_amount
            )
            state = AnalysisState(
                run_id=run_id,
                user_input=user_input
            )

            # 5. Run LangGraph Pipeline with PostgreSQL Checkpointer and graceful fallback
            logger.info("Invoking LangGraph pipeline execution")
            db_url = settings.db.url
            try:
                logger.info("Connecting to PostgreSQL checkpointer database", db_url=db_url)
                async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
                    await checkpointer.setup()
                    logger.info("Database checkpoint schema successfully validated/created. Executing pipeline...")
                    final_state = await run_pipeline(state, checkpointer=checkpointer)
            except Exception as db_err:
                logger.error("Failed to connect or setup PostgreSQL checkpoint store. Falling back to in-memory non-persistent execution", error=str(db_err))
                # Fallback to default in-memory run without checkpointer
                final_state = await run_pipeline(state, checkpointer=None)


            # # 6. Extract results from pipeline final state
            # company_data = final_state.company.model_dump() if final_state.company else {}
            # market_data = final_state.market.model_dump() if final_state.market else {}
            # founders_data = [f.model_dump() for f in final_state.founders] if final_state.founders else []
            # finance_data = final_state.finance.model_dump() if final_state.finance else {}
            # competitors_data = final_state.competitive.model_dump() if final_state.competitive else {}

            # report = {
            #     "startup_name": startup_name,
            #     "status": "completed",
            #     "metadata": {
            #         "sector": industry_sector,
            #         "stage": stage_enum.value if stage_enum else None,
            #         "requested_amount": requested_amount,
            #         "file_processed": file_path
            #     },
            #     "analysis": {
            #         "company_profile": company_data,
            #         "market_analysis": market_data,
            #         "founders": founders_data,
            #         "financial_metrics": finance_data,
            #         "competitive_landscape": competitors_data,
            #         "agent_run_statuses": final_state.agent_statuses
            #     }
            # }

            logger.info("Pipeline executed successfully. Dispatching success callback.")
            await self.send_webhook(
                run_id,
                event_type="pipeline_success",
                status="completed",
                message="Analysis pipeline completed successfully!",
                data={} # report
            )

        except ValueError as ve:
            # Input validation and format errors (safe to show to the user)
            logger.error("Analysis pipeline failed due to validation/input error", error=str(ve))
            await self.send_webhook(
                run_id,
                event_type="pipeline_failed",
                status="failed",
                message=str(ve)
            )
            raise ve
        except Exception as e:
            # Unexpected system errors (log internally, send generic high-level message to user)
            logger.error("Analysis pipeline execution encountered an unexpected system error", error=str(e), exc_info=True)
            await self.send_webhook(
                run_id,
                event_type="pipeline_failed",
                status="failed",
                message="An unexpected error occurred during the analysis pipeline execution. Please try again later or contact support."
            )
            # Re-raise so server logs show the traceback
            raise e

        finally:
            # 7. Stateless Isolation Cleanup (Option A)
            if sandbox_dir.exists():
                try:
                    shutil.rmtree(sandbox_dir)
                    logger.info("Isolated sandbox directory cleaned up successfully")
                except Exception as ex:
                    logger.error("Failed to clean up sandbox directory during cleanup sweep", error=str(ex))
