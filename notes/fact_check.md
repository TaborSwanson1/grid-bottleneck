# Fact check (Day 11, October 30, 2026)

Every "reported" number in the project plan, checked against the original source where I could get it. Status: **Confirmed**, **Corrected** (the original says something different), **Secondary** (confirmed only through coverage of the original), or **Cut** (couldn't trace it).

## Transformers

| Claim in old plan | Status | What the source says | Source |
|---|---|---|---|
| 30% power transformer shortfall, 2025 | Confirmed | 30% deficit, described as "currently" | Wood Mackenzie, Aug 13, 2025 |
| 10% distribution transformer shortfall | **Corrected** | 6% | Wood Mackenzie, Aug 13, 2025 (pv magazine said 10%) |
| About 15% shortfall in 2026 | **Cut** | Not found in POWER, pv magazine or Wood Mackenzie | none |
| Imports 80% of power, 50% of distribution | Confirmed | Same | Wood Mackenzie |
| Power transformer demand up 119% since 2019 | **Corrected** | 116% (GSU 274%, distribution 30% to 80%) | Wood Mackenzie (pv magazine said 119%) |
| Distribution demand up 41% | **Corrected** | 30% to 80%, by specification | Wood Mackenzie |
| (new) Prices since 2019 | Added | Power +77%, distribution +78% to 95%, GSU +45% | Wood Mackenzie |
| Power transformer lead time 128 weeks, Q2 2025 | Secondary | 128 weeks; GSU 144 weeks | POWER, Jan 2, 2026, citing Wood Mackenzie Q2 2025 survey |
| EHV units up to five years | **Cut** | Not found; POWER says large units "remain above two years" | none |
| Distribution lead times about 30 weeks by mid-2025 | Secondary | 30 weeks by Q2 2025 | CRS R48933 (Apr 2026), citing Wood Mackenzie |
| NREL: prices up 5 to 6 times in 2 years | **Corrected** | Report PDF: 4 to 9 times over 3 years. Summary page: 5 to 6 times over 2 years | NREL/TP-6A40-87653 |
| NREL: lead times up to 2 years, 4x pre-2022 | Confirmed | Same | NREL/TP-6A40-87653 |
| (new) BLS PPI up ~40% 2020 to 2024, inflation-adjusted | Added | Distribution and large power transformers | CRS R48933 |

## Policy

| Claim | Status | What the source says | Source |
|---|---|---|---|
| EO 14420, signed Aug 26, 2026 | **Corrected** | **EO 14421**, first numbered 14420. Signed Aug 26, 2026 | White House text; McGuireWoods |
| Targets China and "foreign adversaries" | **Corrected** | "Covered foreign entities": countries under US arms embargoes or sanctions (ITAR 126.1), which includes China, or parties DOE flags. "Foreign adversary" isn't in the text | White House text |
| Doesn't ban anything by itself; DOE blocks purchases | Confirmed, expanded | DOE can prohibit, condition, or order replacement, including equipment already installed. Substation transformers are named. Rules due Dec 24, 2026 | White House text; DOE RFI 2026-18370 |
| 2020 order led to a DOE ban aimed at China, later revoked | Confirmed | DOE order of Dec 17, 2020; suspended Jan 20, 2021; revoked Apr 20, 2021 | Federal Register 2021-08483; Sidley |
| Finished transformers not under Section 232; parts may be | Partly confirmed | Cores and laminations added to the 50% Section 232 steel tariff on Aug 15, 2025. No source on finished units | CRS R48933 |

## Data centers

| Claim | Status | What the source says | Source |
|---|---|---|---|
| ~$5B of GB300 racks in August, ~$3B/month after | Secondary | Same, from Business Insider (internal email) | Gadget Review, Oct 21, 2026; TIKR |
| Sites had room but no power | Secondary | Same | Gadget Review; TIKR |
| "Early Rack Receipt" | Secondary | Same | Gadget Review; TIKR |
| AWS CFO said FCF went negative | Secondary | CFO John Felton, internal September meeting | Gadget Review, citing Business Insider |
| Amazon: "best business practice" | Secondary | Spokesperson statement; Amazon disputed the story | Gadget Review; TIKR |
| $200 to $300B of AI chips sitting idle | **Cut** | Not in any coverage checked | none |
| 2026 capex ~$220B; demand ahead of capacity | Confirmed | Said on the Oct 29, 2026 call | Call transcript (see `amazon_q3_2026_call.md`) |

## Anthropic S-1 (checked in the filing itself)

| Claim | Status | Filing |
|---|---|---|
| Nasdaq, "ANT" | Confirmed | Cover page |
| H1 2026 revenue $16.3B vs $1.2B | Confirmed | $16,286M vs $1,163M |
| Q2 revenue $11.6B | Confirmed | $11,555M |
| H1 net loss $80.7B, mostly non-cash | Confirmed | $80,748M; $72,388M is change in fair value of convertible notes, derivatives and SAFEs |
| Q2 operating income $974M | Confirmed | $974M (8% margin). But H1 was a $693M operating loss |
| Cash from operations positive | Confirmed | $3,929M for H1 2026 |
| Compute and infrastructure $8.95B | Confirmed | $8,945M |
| Gross margin about 85% | **Cut** | Not reported. Anthropic dropped gross profit from its statements in 2025 |
| Amazon commitment $110B, 2026 to 2036 | Confirmed | At least $110.0B, May 2026 to April 2036 |
| Google commitment $114.5B, 2026 to 2033 | Confirmed | About $114.5B, April 2026 to July 2033 |
| Total commitments $417B to $637B | Partly confirmed | ~$417B of future minimum payments on new lease and compute deals. $637B not found |

## Sources

- [Wood Mackenzie: Transformer troubles (Aug 13, 2025)](https://www.woodmac.com/ja/news/opinion/transformer-troubles-manufacturing-and-policy-constraints-hit-us-transformer-supply/)
- [pv magazine: Wood Mackenzie on supply deficits (Aug 14, 2025)](https://pv-magazine-usa.com/2025/08/14/grid-transformers-face-significant-supply-deficits-says-wood-mackenzie/)
- [POWER: Transformers in 2026 (Jan 2, 2026)](https://www.powermag.com/transformers-in-2026-shortage-scramble-or-self-inflicted-crisis)
- [NREL report 87653 (PDF)](https://www.nrel.gov/docs/fy24osti/87653.pdf)
- [CRS R48933: Electricity Distribution Transformers (Apr 2026)](https://www.everycrsreport.com/files/2026-04-23_R48933_e69524fc8f52951a242ed35c91713fade25fe8ac.html)
- [White House: Declaring a National Emergency to Secure the US Bulk-Power System](https://www.whitehouse.gov/presidential-actions/2026/08/declaring-a-national-emergency-to-secure-the-united-states-bulk-power-system/)
- [McGuireWoods: DOE RFI under EO 14421](https://www.mcguirewoods.com/client-resources/alerts/2026/9/doe-issues-request-for-information-on-securing-u-s-bulk-power-system-under-executive-order-14421/)
- [Federal Register: DOE RFI 2026-18370](https://public-inspection.federalregister.gov/2026-18370.pdf)
- [Federal Register 2021-08483: revocation of the 2020 prohibition order](https://www.govinfo.gov/content/pkg/FR-2021-04-22/html/2021-08483.htm)
- [Sidley: DOE revokes prohibition order (Apr 2021)](https://www.sidley.com/en/insights/newsupdates/2021/04/department-of-energy-revokes-prohibition-order)
- [Gadget Review: Amazon warehousing chips it can't power (Oct 21, 2026)](https://www.gadgetreview.com/amazon-is-warehousing-billions-in-nvidia-ai-chips-it-cannot-yet-power-up)
- [TIKR: what Amazon's Oct 29 call has to prove](https://www.tikr.com/blog/some-of-amazons-new-ai-servers-are-reportedly-waiting-on-power-heres-what-october-29-has-to-prove)
- [Anthropic S-1 on SEC EDGAR](https://www.sec.gov/Archives/edgar/data/0002130357/000162828026067168/anthropicpbc-sx1.htm)
