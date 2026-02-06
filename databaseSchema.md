erDiagram
    experiment {
        INTEGER exid PK
        TEXT name
        TEXT crop FK
    }

    operations {
        INTEGER opID PK
        INTEGER o_t_exid FK
        TEXT name
        TEXT odate
    }

    treatment {
        INTEGER tid PK
        INTEGER t_exid FK
        TEXT name
    }

    Irrig_floodH {
        INTEGER opID FK
    }
    Irrig_floodR {
        INTEGER opID FK
    }
    Irrig_pivotOp {
        INTEGER opID FK
    }
    PGROp {
        INTEGER opID PK,FK
    }
    fertNutOp {
        INTEGER opID FK
    }
    fertilizationOp {
        INTEGER opID FK
    }
    initCondOp {
        INTEGER opID PK,FK
    }
    irrigationDetails {
        INTEGER opID FK
    }
    surfResOp {
        INTEGER opID PK,FK
    }
    tillageOp {
        INTEGER opID PK,FK
    }

    experiment ||--o{ operations : contains
    experiment ||--o{ treatment : has
    operations ||--o{ Irrig_floodH : has_details
    operations ||--o{ Irrig_floodR : has_details
    operations ||--o{ Irrig_pivotOp : has_details
    operations ||--o{ PGROp : defines
    operations ||--o{ fertNutOp : defines
    operations ||--o{ fertilizationOp : defines
    operations ||--o{ initCondOp : defines
    operations ||--o{ irrigationDetails : has_details
    operations ||--o{ surfResOp : defines
    operations ||--o{ tillageOp : defines
