// Institutional Typst Investment Memo Template
#set document(title: "Institutional Investment Memo")
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
  header: align(right, text(8pt, fill: gray, font: "Liberation Serif")[CONFIDENTIAL & PROPRIETARY]),
  footer: [
    #align(center)[
      #text(8pt, fill: gray, font: "Liberation Serif")[Page #counter(page).display()]
    ]
  ]
)
#set text(font: "Liberation Serif", size: 10.5pt, fill: rgb("111111"))
#set par(justify: true, leading: 0.65em)

// Typography rules
#show heading: set text(fill: rgb("1a1a1a"), font: "Liberation Serif")
#set heading(numbering: "1.")

// Title Block
#align(center)[
  #v(1em)
  #text(size: 16pt, weight: "bold", font: "Liberation Serif")[INVESTMENT COMMITTEE MEMORANDUM]
  #v(0.5em)
  #line(length: 100%, stroke: 1.5pt + rgb("000000"))
]

#v(1em)

#grid(
  columns: (120pt, 1fr),
  row-gutter: 1.2em,
  [*TO:*], [Investment Committee],
  [*DATE:*], [May 25, 2026],
  [*RECOMMENDATION:*], [
    #text(weight: "bold", fill: if "{{ recommendation.verdict }}" == "invest" { rgb("10b981") } else if "{{ recommendation.verdict }}" == "watch" { rgb("f59e0b") } else { rgb("ef4444") })[
      {{ recommendation.verdict | upper }}
    ]
  ],
  [*CONVICTION SCORE:*], [{{ recommendation.conviction_score }} / 10],
)

#v(1em)
#line(length: 100%, stroke: 0.5pt + gray)
#v(1.5em)

// Render factual sections
{% if sections_map.executive_summary %}
= Executive Summary
{{ sections_map.executive_summary.content }}
{% endif %}

{% if sections_map.market_analysis %}
= Market Sizing & CAGR Analysis
{{ sections_map.market_analysis.content }}
{% endif %}

{% if sections_map.competitive_landscape %}
= Competitive Landscape
{{ sections_map.competitive_landscape.content }}
{% endif %}

{% if sections_map.team_assessment %}
= Team Assessment & Fit
{{ sections_map.team_assessment.content }}
{% endif %}

{% if sections_map.due_diligence_notes %}
= Due Diligence & Metrics Verification
{{ sections_map.due_diligence_notes.content }}
{% endif %}

// Render investment recommendations
{% if recommendation %}
= Final Recommendation & Balanced Synthesis

== Investment Thesis
{{ recommendation.investment_thesis }}

#v(1em)

#grid(
  columns: (1fr, 1fr),
  gutter: 20pt,
  box(
    stroke: 0.5pt + rgb("10b981"),
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    [
      #text(weight: "bold", fill: rgb("10b981"))[Key Strengths]
      #v(0.5em)
      {% for str in recommendation.key_strengths %}
      - {{ str }}
      {% endfor %}
    ]
  ),
  box(
    stroke: 0.5pt + rgb("ef4444"),
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    [
      #text(weight: "bold", fill: rgb("ef4444"))[Critical Risks]
      #v(0.5em)
      {% for r in recommendation.key_risks %}
      - {{ r }}
      {% endfor %}
    ]
  )
)

#v(1em)

#grid(
  columns: (1fr, 1fr),
  gutter: 20pt,
  box(
    stroke: 0.5pt + rgb("3b82f6"),
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    [
      #text(weight: "bold", fill: rgb("3b82f6"))[Growth Directives (DO)]
      #v(0.5em)
      {% for act in recommendation.do_list %}
      - {{ act }}
      {% endfor %}
    ]
  ),
  box(
    stroke: 0.5pt + rgb("f59e0b"),
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    [
      #text(weight: "bold", fill: rgb("f59e0b"))[Risk Directives (STOP)]
      #v(0.5em)
      {% for act in recommendation.stop_list %}
      - {{ act }}
      {% endfor %}
    ]
  )
)

#v(1.5em)

{% if recommendation.fund_fit_note %}
*Fund Thesis Fit Note:* \
{{ recommendation.fund_fit_note }}
{% endif %}

#v(0.5em)

{% if recommendation.conditions %}
== Closing Conditions Checklist
{% for cond in recommendation.conditions %}
- [ ] {{ cond }}
{% endfor %}
{% endif %}

{% if recommendation.next_steps %}
== Downstream Analyst Steps
{% for ns in recommendation.next_steps %}
- {{ ns }}
{% endfor %}
{% endif %}

{% endif %}
