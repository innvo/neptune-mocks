# Name

## Mapping

node

*   Arrays must be enclosed by " and delimited by ;

| neptune | LPG V11 | GDS | Notes |
| --- | --- | --- | --- |
| ~id | NODE\_ID | NODE\_ID | GUID |
| name\_full:String | NODE\_NAME | NODE\_NAME |   |
|   | NAME\_LIST:NAME\_FIRST, NAME\_LIST:NAME\_MIDDLE, NAME\_LIST:NAME\_LAST, NAME\_LIST:NAME\_TYPE | NAME\_LIST:NAME\_FIRST, NAME\_LIST:NAME\_MIDDLE, NAME\_LIST:NAME\_LAST, NAME\_LIST:NAME\_TYPE | MVP not planning to implement NAME\_LIST all names will be NAME\_FULL |
| ~label | NODE\_TYPE | NODE\_TYPE | name, recall, precision |

## edges

### person\_name

<table><tbody><tr><td>neptune</td><td>LPGV11</td><td>GDS</td><td>Notes</td></tr><tr><td>~is</td><td>EDGE_ID</td><td>EDGE_ID</td><td>GUID</td></tr><tr><td>~from</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>person</td></tr><tr><td>~to</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>name</td></tr><tr><td>name_full:String</td><td>EDGE_NAME</td><td>EDGE_NAME</td><td>isAssociatedWithName</td></tr><tr><td>~label</td><td>EDGE_TYPE</td><td>EDGE_TYPE</td><td>person_name</td></tr></tbody></table>