# Form

## Mapping

node

*   Arrays must be enclosed by " and delimited by ;

| neptune | LPG V11 | GDS | Notes |
| --- | --- | --- | --- |
| ~id | NODE\_ID | NODE\_ID | GUID |
| receipt\_number:String | NODE\_NAME, RECEIPT\_NUMBER | NODE\_NAME, {RECEIPT\_NUMBER} |   |
| form\_number:String | FORM\_NUMBER | {FORM.NUMBER} |   |
| receipt\_date\_estimated:Date | RECEIPT\_DATE\_ESTIMATED | {RECEIPT\_DATE\_ESTIMATED} |   |
| status:String | STATUS | {STATUS} |   |
| principal\_application\_receipt\_number:String | PRINCIPAL\_APPLICANT\_RECEIPT\_NUMBER | {PRINCIPAL\_APPLICANT\_RECEIPT\_NUMBER} |   |
| source\_table:String | SOURCE\_TABLE | {SOURCE\_TABLE} |   |
| source\_id:String | SOURCE\_ID | {SOURCE\_ID) |   |
| ~label | NODE\_TYPE | NODE\_TYPE | form |

## edges

### person\_form

<table><tbody><tr><td>neptune</td><td>LPGV11</td><td>GDS</td><td>Notes</td></tr><tr><td>~is</td><td>EDGE_ID</td><td>EDGE_ID</td><td>GUID</td></tr><tr><td>~from</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>person</td></tr><tr><td>~to</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>name</td></tr><tr><td>name_full:String</td><td>EDGE_NAME</td><td>EDGE_NAME</td><td>isAssociatedWithName</td></tr><tr><td>~label</td><td>EDGE_TYPE</td><td>EDGE_TYPE</td><td>person_name</td></tr></tbody></table>