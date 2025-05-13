# Receipt

## Mapping

node

*   Arrays must be enclosed by " and delimited by ;

| neptune | LPG V11 | GDS | Notes |
| --- | --- | --- | --- |
| ~id | NODE\_ID | NODE\_ID | GUID |
| receipt\_number:String | NODE\_NAME, RECEIPT\_NUMBER | NODE\_NAME, {RECEIPT\_NUMBER} |   |
| ~label | NODE\_TYPE | NODE\_TYPE | receipt |

## edges

### rfromreceipt

<table><tbody><tr><td>neptune</td><td>LPGV11</td><td>GDS</td><td>Notes</td></tr><tr><td>~is</td><td>EDGE_ID</td><td>EDGE_ID</td><td>GUID</td></tr><tr><td>~from</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>person</td></tr><tr><td>~to</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>receipt</td></tr><tr><td>name_full:String</td><td>EDGE_NAME</td><td>EDGE_NAME</td><td>groupedWith</td></tr><tr><td>~label</td><td>EDGE_TYPE</td><td>EDGE_TYPE</td><td>form_receipt</td></tr></tbody></table>