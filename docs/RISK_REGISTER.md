# Risk Register

| Risk | Impact | Mitigation/monitor |
|---|---|---|
| Terms change | Incorrect estimate | Effective dates, freshness queue, source hash |
| Wrong variant | Wrong rules | Exact identity, variant tests |
| Cap bug | Overstated rewards | Typed cap scope and boundary tests |
| AI hallucination | Misinformation | RAG, citation validation, abstention |
| Point value overstated | Misleading comparison | User assumptions and sensitivity |
| Unknown cap usage | False precision | Explicit unknown/range |
| Optimizer misses threshold | Suboptimal allocation | Constraint model and adversarial tests |
| Source rights unclear | Legal risk | Rights review and minimum excerpts |
| Excess data | Privacy risk | Minimization, retention, deletion |
| Guarantee implied | Trust risk | Clear estimate copy and source dates |
| AI outage | Assistant unavailable | Isolated optional subsystem |
| Untraceable rule change | Irreproducible result | Versions, manifests, audit |
| Dependency compromise | Security risk | Lockfiles and scanning |
| Backup restore fails | Data loss | Restore drills |

Assign owners, likelihood, severity, and mitigation status before each production release.
