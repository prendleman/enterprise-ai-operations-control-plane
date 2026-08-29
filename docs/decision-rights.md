# Decision Rights (RACI-style)

Roles: AI Operations (AO), Security (SEC), Privacy (PRI), Enterprise Architecture (EA), Engineering (ENG), Business Owner (BO), Finance/FinOps (FIN), Legal (LEG), Platform (PLT).

| Decision | AO | SEC | PRI | EA | ENG | BO | FIN | LEG | PLT |
| -------- | -- | --- | --- | -- | --- | -- | --- | --- | --- |
| Model approval | A | C | C | C | C | I | I | C | R |
| Production eligibility | A | C | C | C | R | A | C | C | C |
| Restricted-data access | C | A | A | C | R | C | I | C | C |
| Agent autonomy level | A | C | I | C | R | C | I | I | C |
| Budget exceptions | C | I | I | I | C | C | A | I | I |
| Sandbox access | A | C | C | I | R | C | C | I | R |
| Production exceptions | A | A | C | C | R | C | C | C | C |

R = Responsible, A = Accountable, C = Consulted, I = Informed.

This matrix is a reference operating-model artifact for the prototype, not an organizational mandate.
