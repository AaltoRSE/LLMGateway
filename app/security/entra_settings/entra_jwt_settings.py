role_map = {
    # Degree students
    "f92054ea-0968-47f1-bce8-9c0f94d65f1e": "student_degree",
    # Non-degreeStudents
    "c88ee157-1332-4467-9bf6-4f518408dfa2": "student_nonDegree",
    # Staff
    "3ab7ddd2-16f3-4736-853c-f1f7f2c00c68": "staff",
    # Ext-staff
    "f8d2cdc4-c675-48b6-afc3-f75ee7fce42d": "staff_ext",
    # Student group AzAAIA_MARK-C0065
    "69a0bbf2-3f37-458c-810e-d8457cb2a9e3": "student_degree",
    # Student group CS-E012-students
    "c6dcb3fd-1817-4131-bd81-f37746215f08": "student_degree",
    # Student group Yritysvastuu2025
    "1d7565cf-499d-4c54-9624-0651cb9e6369": "student_degree",
    # Student group MLI-C1208
    "cadb0e65-e384-4054-bac6-cb9505a1956b": "student_degree",
    # Early students: bachelor's and master's thesis workers and doctoral researchers
    "edbeff91-66b4-4db5-b399-f9c3a3cbccf4": "student_degree",
    # Abacus group -     Abacus_ERP_PROD_USERS
    "b050d1ca-73db-4045-8534-6288a93dab89": "abacus",
    # Abacus group - -   Abacus_EPM_PROD_USERS
    "be5ca02a-b60b-4cfe-84ec-9430fbd525a5": "abacus",
}

# Initialize auth service
# NOTE: do not use the auth_service here but rather get a reference through get_entrajwt_auth_service call

tenant_id = ("ae1a7724-4041-4462-a6dc-538cb199707e",)  # Aalto's tenant ID
audience = (
    "api://f9f02fa3-9d55-422b-9dd1-1942471b27c4",
)  # SECURITY: app which is permitted, do not change!
valid_scopes = (["AaltoAI.Access"],)  # SECURITY: Do not change!
