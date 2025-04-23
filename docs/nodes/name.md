# Name

## Mapping

node

*   Arrays must be enclosed by " and delimited by ;

| neptune | LPG V11 | GDS \* JSON NODE\_PROPERTIES | Notes |
| --- | --- | --- | --- |
| ~id | NODE\_ID | NODE\_ID | GUID |
| name\_full:String | NODE\_NAME | NODE\_NAME |   |
| name\_full\_list:String\[\] | NAME\_FULL\_LIST:NAME\_FULL | NAME\_FULL\_LIST:NAME\_FULL |   |
| NAME\_FULL\_LIST:COUNT | MVP not planning to implement COUNT for neptune due to array complexity |   |   |
| name\_full\_alias:String\[\] | NAME\_FULL\_ALIAS\_LIST:NAME\_FULL |   |   |
| NAME\_FULL\_ALIAS\_LIST:NAME\_TYPE | NAME\_FULL\_ALIAS\_LIST:NAME\_FULL |   |   |
| NAME\_FULL\_ALIAS\_LIST:NAME\_TYPE | MVP not planning to implement NAME\_TYPE for neptune due to array complexity |   |   |
|   | NAME\_LIST:NAME\_FIRST |   |   |
| NAME\_LIST:NAME\_MIDDLE |   |   |   |
| NAME\_LIST:NAME\_LAST |   |   |   |
| NAME\_LIST:NAME\_TYPE | NAME\_LIST:NAME\_FIRST |   |   |
| NAME\_LIST:NAME\_MIDDLE |   |   |   |
| NAME\_LIST:NAME\_LAST |   |   |   |
| NAME\_LIST:NAME\_TYPE | MVP not planning to implement NAME\_LIST all names will be NAME\_FULL format |   |   |
| role\_type\_list:String\[\] | ROLE\_TYPE\_LIST:ROLE\_TYPE |   |   |
| ROLE\_TYPE\_LIST:ROLE\_COUNT | ROLE\_TYPE\_LIST:ROLE\_TYPE |   |   |
| ROLE\_TYPE\_LIST:COUNT | MVP not planning to implement COUNT for neptune due to array complexity |   |   |
| birth\_date:Date | BIRTH\_DATE | BIRTH\_DATE |   |
| birth\_date\_list:Date\[\] | BIRTH\_DATE\_LIST | BIRTH\_DATE\_LIST |   |
| birth\_country:String | BIRTH\_COUNTRY | BIRTH\_COUNTRY |   |
| birth\_country\_list:String\[\] | BIRTH\_COUNTRY\_LIST | BIRTH\_COUNTRY\_LIST |   |
| gender\_list:String\[\] | GENDER\_LIST:GENDER | GENDER\_LIST:GENDER |   |
| GENDER\_LIST:COUNT | MVP not planning to implement COUNT for neptune due to array complexity |   |   |
| anumber\_primary:String | ANUMBER\_NUMBER\_PRIMARY | ANUMBER\_NUMBER\_PRIMARY |   |
| anumber\_list:String\[\] | ANUMBER\_LIST:ANUMBER | ANUMBER\_LIST:ANUMBER |   |
| ANUMBER\_NUMBER\_LIST:IS\_PRIMARY | MVP not planning to implement IS\_PRIMARY for neptune due to array complexity |   |   |
| fingerprint\_identification\_number\_list:String\[\] | FINGERPRINT\_IDENTIFICATION\_NUMBER\_LIST: |   |   |
| FINGERPRINT\_IDENTIFICATION\_NUMBER | FINGERPRINT\_IDENTIFICATION\_NUMBER\_LIST: |   |   |
| FINGERPRINT\_IDENTIFICATION\_NUMBER |   |   |   |
| social\_security\_number\_list:String\[\] | SOCIAL\_SECURITY\_NUMBER\_LIST: |   |   |
| SOCIAL\_SECURITY\_NUMBER | SOCIAL\_SECURITY\_NUMBER\_LIST: |   |   |
| SOCIAL\_SECURITY\_NUMBER |   |   |   |
| passport\_number\_list:String\[\] | PASSPORT\_NUMBER\_LIST: |   |   |
| PASSPORT\_NUMBER | PASSPORT\_NUMBER\_LIST: |   |   |
| PASSPORT\_NUMBER |   |   |   |
| ~label | NODE\_TYPE | NODE\_TYPE | person, recall, precision |

## edges

### person\_name

<table><tbody><tr><td>neptune</td><td>LPGV11</td><td>GDS * JSON _PROPERTIES</td><td>Notes</td></tr><tr><td>~is</td><td>EDGE_ID</td><td>EDGE_ID</td><td>GUID</td></tr><tr><td>~from</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>&nbsp;</td></tr><tr><td>~to</td><td>NODE_ID_FROM</td><td>NODE_ID_FROM</td><td>&nbsp;</td></tr><tr><td>name_full:String</td><td>EDGE_NAME</td><td>EDGE_NAME</td><td>isAssociatedWithName</td></tr><tr><td>~label</td><td>EDGE_TYPE</td><td>EDGE_TYPE</td><td>person_name</td></tr></tbody></table>