# Overbuild signals (November 2, 2026)

The thesis: data center projects are committed on today's demand, take years to deliver, and get locked in for 15 to 20 years. Developers pile in at the same time. If the market shifts before delivery, some of it ends up stranded. This file collects the evidence for and against, one signal at a time.

The claim this supports is a **timing risk**, not a prediction of a crash. Demand today is strong (Northern Virginia 0.2% vacant, AWS up 39%), which is also what the early part of a build cycle looks like.

## 1. Commitments piling up faster than deliveries

Signed-but-not-started lease payments divided by payments on leases already running (both undiscounted). Chart: `charts/lease_backlog_ratio.png`. Data: `data/clean/lease_backlog_ratio.csv`.

| Company | 2022 | Latest | Direction |
|---|---|---|---|
| Oracle | n/a | 4.6x (Aug 2026) | Down from 6.9x (Feb 2026) as buildings get handed over |
| Alphabet | 0.2x | 4.5x (Sep 2026) | Rising |
| Meta | 0.6x | 3.0x (Dec 2025) | Rising |
| Microsoft | 0.4x | 2.8x (Sep 2026) | Rising again after a 2025 dip |
| Amazon | 0.4x | 1.2x (Sep 2026) | Rising slowly; includes warehouses |
| CoreWeave | n/a | 1.2x (Jun 2026) | Down from 6.0x as leases start |

**Read:** at four of six, signed commitments are growing faster than delivered capacity. Oracle and CoreWeave show deliveries catching up, which cuts against a stuck backlog there.

## 2. A few buyers carry much of it

| Fact | Source |
|---|---|
| Microsoft booked $10.0B of revenue from OpenAI in the September 2026 quarter, about 11% of its $92.3B total | Microsoft 10-Q, Sep 30, 2026 |
| Microsoft's commercial contracted backlog rose 73% to $677B | Microsoft 10-Q |
| Amazon's contracted backlog is about $578B. OpenAI ($38B plus a $100B expansion over 8 years) and Anthropic ($110B per its S-1) add up to roughly 40% of it. Rough: deal timing differs | Amazon 10-Q, Sep 30, 2026; Anthropic S-1 |
| Oracle's backlog went from $455B to $664B in a year, "primarily attributable to certain significant cloud contracts." No customer named | Oracle 10-Q, Aug 31, 2026 |
| CoreWeave's three largest customers were 72% of revenue in Q2 2026. The largest was 36%, down from 71% a year earlier | CoreWeave 10-Q, Jun 30, 2026 |
| Anthropic signed about $417B of new compute and lease commitments, against about $46B a year of revenue at its Q2 2026 pace (about 9x). Its cloud commitments are owed "regardless of actual usage" | Anthropic S-1 |

**Read:** much of the backlog depends on two or three AI labs that are still raising money. If one of them slows down, the commitments don't vanish. They become a credit problem for whoever is owed.

## 3. Signs the market shifts mid-build

| Signal | What happened | Supports thesis? | Source |
|---|---|---|---|
| Lease cancellations | Early 2025: Microsoft reportedly cancelled about 200 MW of US leases and let over 1 GW of agreements lapse, partly as OpenAI moved work to Oracle. Microsoft didn't comment. By late 2026 its signed backlog was $365B | Yes. Plans reversed and then reversed again inside one build cycle, and work moved between providers | TD Cowen via Bloomberg and others |
| Server lives | Amazon cut the useful life of some servers from 6 to 5 years in 2025 | Yes. Hardware ages faster than the 15 to 20 year leases around it | Amazon 2025 10-K |
| Server lives | Meta extended most server lives to about 5.5 years in 2025 | No. Cuts the other way | Meta 2025 10-K |
| GPU rental prices | On-demand H100 fell from over $7 an hour (early 2024) to about $3 (mid-2026) | Yes, for chips | AIMultiple index, via secondary coverage |
| GPU contract prices | One-year H100 contracts rose about 40%, from $1.70 (Oct 2025) to $2.35 (Mar 2026) | No. Committed demand is still tight | SemiAnalysis, via secondary coverage |
| Pile-in | Only 13% of generation capacity requested 2000 to 2020 ever came online. Texas has about 474 GW of large-load requests (about 90% data centers) against a 91 GW record peak, and paused big approvals for an audit | Yes | LBNL Queued Up 2026; Utility Dive |

## What would change my mind

- The backlog ratio falls everywhere, like Oracle and CoreWeave, meaning deliveries are catching up.
- Contract GPU prices keep rising for another year.
- Large-load queues get audited down and most of what's left gets built.

## Sources

- [Bloomberg: Microsoft dropped some AI data center leases, TD Cowen says](https://www.bloomberg.com/news/articles/2025-02-24/microsoft-cancels-leases-for-ai-data-centers-analyst-says)
- [Network World: Microsoft cancels data center lease plans](https://www.networkworld.com/article/3831799)
- [Latitude Media: are power delays cover for Microsoft's pullback](https://www.latitudemedia.com/news/are-power-delays-a-strategic-cover-for-microsofts-data-center-pullback/)
- [Introl: H100 rental prices](https://introl.com/blog/gpu-cloud-price-collapse-h100-64-percent-drop-2025)
- [Silicon Data: H100 rental price over time](https://www.silicondata.com/blog/h100-rental-price-over-time)
- [Tiger: SemiAnalysis on H100 contract prices](https://www.itiger.com/hans/news/1185188896)
- [Utility Dive: Texas pauses data center interconnections](https://www.utilitydive.com/news/texas-hits-pause-data-center-interconnections/827046/)
- [RTO Insider: ERCOT large load queue](https://www.rtoinsider.com/129421-ercot-large-load-requests-soar-again/)
- Company 10-Qs and 10-Ks and the Anthropic S-1, cached in `data/raw/sec/filings`
