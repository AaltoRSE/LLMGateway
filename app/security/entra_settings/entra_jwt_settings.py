role_map = {
    # Degree students
    "f92054ea-0968-47f1-bce8-9c0f94d65f1e": "entra_user",
    # Non-degreeStudents
    "c88ee157-1332-4467-9bf6-4f518408dfa2": "entra_user",
    # Staff
    "3ab7ddd2-16f3-4736-853c-f1f7f2c00c68": "employee",
    # Ext-staff
    "f8d2cdc4-c675-48b6-afc3-f75ee7fce42d": "entra_user",
    # Student group AzAAIA_MARK-C0065
    "69a0bbf2-3f37-458c-810e-d8457cb2a9e3": "entra_user",
    # Student group CS-E012-students
    "c6dcb3fd-1817-4131-bd81-f37746215f08": "entra_user",
    # Student group Yritysvastuu2025
    "1d7565cf-499d-4c54-9624-0651cb9e6369": "entra_user",
    # Student group MLI-C1208
    "cadb0e65-e384-4054-bac6-cb9505a1956b": "entra_user",
    # Early students: bachelor's and master's thesis workers and doctoral researchers
    "edbeff91-66b4-4db5-b399-f9c3a3cbccf4": "entra_user",
    # Abacus group -     Abacus_ERP_PROD_USERS
    "b050d1ca-73db-4045-8534-6288a93dab89": "entra_user",
    # Abacus group - -   Abacus_EPM_PROD_USERS
    "be5ca02a-b60b-4cfe-84ec-9430fbd525a5": "entra_user",
}

# Initialize auth service
# NOTE: do not use the auth_service here but rather get a reference through get_entrajwt_auth_service call

tenant_id = "ae1a7724-4041-4462-a6dc-538cb199707e"  # Aalto's tenant ID
audience = "api://f9f02fa3-9d55-422b-9dd1-1942471b27c4"
# SECURITY: app which is permitted, do not change!
valid_scopes = ["AaltoAI.Access"]  # SECURITY: Do not change!
