```mermaid
erDiagram
    PERSON ||--o{ PERSON_NAME : has
    PERSON ||--o{ PERSON_ADDRESS : has
    PERSON ||--o{ PERSON_PHONE : has
    PERSON ||--o{ PERSON_ANUMBER : has
    PERSON ||--o{ PERSON_EMAIL : has
    PERSON ||--o{ PERSON_ORGANIZATION : has
    
    NAME ||--o{ PERSON_NAME : belongs_to
    ADDRESS ||--o{ PERSON_ADDRESS : belongs_to
    PHONE ||--o{ PERSON_PHONE : belongs_to
    ANUMBER ||--o{ PERSON_ANUMBER : belongs_to
    EMAIL ||--o{ PERSON_EMAIL : belongs_to
    ORGANIZATION ||--o{ PERSON_ORGANIZATION : belongs_to
    
    PERSON {
       }
    
    NAME {
        int name_id
        string first_name
        string middle_name
        string last_name
        string suffix
        string prefix
    }
    
    ADDRESS {
        int address_id
        string street_line1
        string street_line2
        string city
        string state
        string postal_code
        string country
        boolean is_primary
    }
    
    PHONE {
        int phone_id
        string phone_number
        string type
        boolean is_primary
    }
    
    ANUMBER {
        int anumber_id
        string anumber_value
        string anumber_type
        date issue_date
        date expiry_date
    }
    
    EMAIL {
        int email_id
        string email_address
        boolean is_primary
        boolean is_verified
    }
    
    ORGANIZATION {
        int org_id
        string org_name
        string org_type
        date established_date
    }
    
    PERSON_NAME {
        int person_name_id
        int person_id
        int name_id
        boolean is_primary
        date effective_from
        date effective_to
    }
    
    PERSON_ADDRESS {
        int person_address_id
        int person_id
        int address_id
        string address_type
        date effective_from
        date effective_to
    }
    
    PERSON_PHONE {
        int person_phone_id
        int person_id
        int phone_id
        date effective_from
        date effective_to
    }
    
    PERSON_ANUMBER {
        int person_anumber_id
        int person_id
        int anumber_id
        date effective_from
        date effective_to
    }
    
    PERSON_EMAIL {
        int person_email_id
        int person_id
        int email_id
        date effective_from
        date effective_to
    }
    
    PERSON_ORGANIZATION {
        int person_org_id
        int person_id
        int org_id
        string role
        date joined_date
        date left_date
    }
