# Node Relationship Classification

| node | Relationship Class | GDS-I Release | Mock |
| --- | --- | --- | --- |
| address | Secondary | 1.2 |   |
| building | Primary | 1.0 MVP | Done |
| datainstance | Secondary | 1.0 | WIP |
| email | Secondary | 1.2 |   |
| encounter | Secondary | 1.2 |   |
| form | Secondary | 1.1 |   |
| iperson | Secondary | 1.2 |   |
| name | Primary | 1.0 |   |
| onlineaccount | Primary | 1.1 | Done |
| organization |   |   |   |
| person | Primary |   |   |
| phone |   |   |   |
| receipt | Primary | 1.1 |   |
| socialsecuritynumber | Secondary | TBD |   |

| # | Edge | Relationship Class | GDS-I Release | Mock |
| --- | --- | --- | --- | --- |
| 1. | address\_datainstance | Secondary | 1.2 |   |
| 2. | building\_address | Primary | 1.0 MVP | WIP |
| 3. | encounter\_fingerprintidentificationnumber | Secondary | 1.2 |   |
| 4. | encounter\_receipt | Secondary | 1.2 |   |
| 5. | form\_address\_instance | Secondary | 1.1 |   |
| 6. | form\_receipt | Secondary | 1.1 |   |
| 7. | iperson\_anumber | Secondary | 1.2 |   |
| 8. | iperson\_encounter | Secondary | 1.2 |   |
| 9. | organization\_address | Primary | 1.1 | WIP |
| 10. | organization\_form | Primary | 1.1 |   |
| 11. | organization\_organization | Primary | 1.1 |   |
| 12. | organization\_phone | Primary | 1.1 |   |
| 13. | organization\_receipt | Primary | 1.1 |   |
| 14. | person\_address | Primary | 1.0 MVP | WIP |
| 15. | person\_address\_form | Secondary | 1.1 |   |
| 16. | person\_anumber | Primary | 1.0 MVP | WIP |
| 17. | person\_datainstance | Primary | 1.0 MVP | WIP |
| 18. | person\_email | Primary | 1.0 MVP |   |
| 19. | person\_fingerprintidentificationnumber | Secondary | TBD |   |
| 20. | person\_form | Primary | 1.0 MVP |   |
| 21. | person\_name | Primary | 1.0 MVP |   |
| 22. | person\_onlineaccount | Primary | 1.0 MVP |   |
| 23. | person\_organization | Primary | 1.0 MVP |   |
| 24. | person\_person\_er | Primary | 1.1 |   |
| 25. | person\_person\_form | Secondary | 1.1 |   |
| 26. | person\_phone | Primary | 1.0 MVP |   |
| 27. | person\_phone\_form | Secondary | 1.1 |   |
| 28. | person\_receipt | Secondary | TBD |   |
| 29. | person\_socialsecuritynumber | Secondary | TBD |   |

## Summary

*   **Primary Relationships**: 18 edges (always active)
*   **Secondary Relationships**: 11 edges (user selection required)
*   **Total Edges**: 29 relationship types

### Release Distribution

*   **1.0 MVP**: 9 edges (all Primary)
*   **1.1**: 8 edges (5 Primary, 3 Secondary)
*   **1.2**: 4 edges (all Secondary)
*   **TBD**: 3 edges (all Secondary)y