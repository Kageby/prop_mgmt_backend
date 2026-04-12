from fastapi import FastAPI, Depends, HTTPException, status
from google.cloud import bigquery
from pydantic import BaseModel
import datetime

app = FastAPI()
    
PROJECT_ID = "aesthetic-vent-489415-u9"
DATASET = "property_mgmt"


# ---------------------------------------------------------------------------
# Dependency: BigQuery client
# ---------------------------------------------------------------------------

def get_bq_client():
    client = bigquery.Client()
    try:
        yield client
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

@app.get("/properties", status_code=200)
def get_properties(bq: bigquery.Client = Depends(get_bq_client)):
    """
    Returns all properties in the database.
    """
    query = f"""
        SELECT
            property_id,
            name,
            address,
            city,
            state,
            postal_code,
            property_type,
            tenant_name,
            monthly_rent
        FROM `{PROJECT_ID}.{DATASET}.properties`
        ORDER BY property_id
    """

    try:
        results = bq.query(query).result()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

    properties = [dict(row) for row in results]
    return properties


@app.get("/properties/{property_id}", status_code=200)
def property_by_id(property_id: int, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Returns a single property by ID
    """
    query = f"""
        SELECT
            property_id,
            name,
            address,
            city,
            state,
            postal_code,
            property_type,
            tenant_name,
            monthly_rent
        FROM `{PROJECT_ID}.{DATASET}.properties`
        WHERE property_id = {property_id}
    """

    try:
        results = bq.query(query).result()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

    properties = [dict(row) for row in results]
    return properties


@app.get("/income/{property_id}", status_code=200)
def get_income_by_property(property_id: int, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Returns a single income by property ID
    """
    query = f"""
        SELECT
            income_id,
            property_id,
            amount,
            date,
            description,
        FROM `{PROJECT_ID}.{DATASET}.income`
        WHERE property_id = {property_id}
        ORDER BY date DESC
    """

    try:
        results = bq.query(query).result()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

    income = [dict(row) for row in results]
    return income


# Request body model
class IncomeCreate(BaseModel):
    income_id: int
    amount: float
    date: datetime.date
    description: str

@app.post("/income/{property_id}", status_code=201)
def create_income_record(property_id: int, income_input: IncomeCreate, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Create new income record for a property id
    """
    query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET}.income` (income_id, property_id, amount, date, description) 
        VALUES
        (@income_id, @property_id, @amount, @date, @description) 
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("income_id", "INT64", income_input.income_id),
            bigquery.ScalarQueryParameter("property_id", "INT64", property_id),
            bigquery.ScalarQueryParameter("amount", "FLOAT64", income_input.amount),
            bigquery.ScalarQueryParameter("date", "DATE", income_input.date),
            bigquery.ScalarQueryParameter("description", "STRING", income_input.description)
        ]
    )

    try:
        results = bq.query(query, job_config=job_config).result()
        return {
            "message": "Income record created successfully",
            "income_id": income_input.income_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )


@app.get("/expenses/{property_id}", status_code=200)
def get_expense_by_property(property_id: int, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Returns a single expense by property ID
    """
    query = f"""
        SELECT
            expense_id,
            property_id,
            amount,
            date,
            category,
            vendor,
            description
        FROM `{PROJECT_ID}.{DATASET}.expenses`
        WHERE property_id = {property_id}
        ORDER BY date DESC
    """

    try:
        results = bq.query(query).result()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

    expenses = [dict(row) for row in results]
    return expenses


# Request body model
class ExpenseCreate(BaseModel):
    expense_id: int
    amount: float
    date: datetime.date
    category: str
    vendor: str
    description: str

@app.post("/expenses/{property_id}", status_code=201)
def create_expense_record(property_id: int, expense_input: ExpenseCreate, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Create new expense record for a property id
    """
    query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET}.expenses` (expense_id, property_id, amount, date, category, vendor, description) 
        VALUES
        (@expense_id, @property_id, @amount, @date, @category, @vendor, @description) 
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("expense_id", "INT64", expense_input.expense_id),
            bigquery.ScalarQueryParameter("property_id", "INT64", property_id),
            bigquery.ScalarQueryParameter("amount", "FLOAT64", expense_input.amount),
            bigquery.ScalarQueryParameter("date", "DATE", expense_input.date),
            bigquery.ScalarQueryParameter("category", "STRING", expense_input.category),
            bigquery.ScalarQueryParameter("vendor", "STRING", expense_input.vendor),
            bigquery.ScalarQueryParameter("description", "STRING", expense_input.description),
        ]
    )

    try:
        results = bq.query(query, job_config=job_config).result()
        return {
            "message": "Expense record created successfully",
            "expense_id": expense_input.expense_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )    


@app.delete("/income/{income_id}", status_code=200)
def delete_income_record(income_id: int, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Delete an income record by property ID
    """
    query = f"""
        DELETE FROM `{PROJECT_ID}.{DATASET}.income`
        WHERE income_id = {income_id}
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("income_id", "INT64", income_id),
        ]
    )

    try:
        job = bq.query(query, job_config=job_config)
        job.result()

        if job.num_dml_affected_rows == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Income record with id {income_id} not found"
            )
        return {
            "message": "Income record deleted successfully",
            "income_id": income_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@app.delete("/expenses/{expense_id}", status_code=200)
def expense_by_property_id(expense_id: int, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Delete an expense record by property ID
    """
    query = f"""
        DELETE FROM `{PROJECT_ID}.{DATASET}.expense`
        WHERE expense_id = {expense_id}
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("expense_id", "INT64", expense_id),
        ]
    )

    try:
        job = bq.query(query, job_config=job_config)
        job.result()

        if job.num_dml_affected_rows == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense record with id {income_id} not found"
            )
        return {
            "message": "Expense record deleted successfully",
            "expense_id": expense_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# Request body model
class IncomeUpdate(BaseModel):
    amount: float
    date: datetime.date
    description: str

@app.put("/income/{income_id}", status_code=200)
def update_income_record(income_id: int, income_input: IncomeUpdate, bq: bigquery.Client = Depends(get_bq_client)):
    """
    Update an income record
    """
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET}.income`
        SET
            amount = @amount,
            date = @date,
            description = @description
        WHERE income_id = {income_id}
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("income_id", "INT64", income_id),
            bigquery.ScalarQueryParameter("amount", "FLOAT64", income_input.amount),
            bigquery.ScalarQueryParameter("date", "DATE", income_input.date),
            bigquery.ScalarQueryParameter("description", "STRING", income_input.description)
        ]
    )

    try:
        results = bq.query(query, job_config=job_config).result()
        return {
            "message": "Income record updated successfully",
            "income_id": income_id,
            "updated_data": income_input
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )


# Request body model
class ExpenseUpdate(BaseModel):
    amount: float
    date: datetime.date
    category: str
    vendor: str
    description: str
    
@app.put("/expense/{expense_id}", status_code=200)
def update_expense_record(expense_id: int, expense_input: ExpenseUpdate,bq: bigquery.Client = Depends(get_bq_client)):
    """
    Update an expense record
    """
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET}.expense`
        SET
            amount = @amount,
            date = @date,
            category = @category,
            vendor = @vendor,
            description = @description
        WHERE expense_id = {expense_id}
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("expense_id", "INT64", expense_id),
            bigquery.ScalarQueryParameter("amount", "FLOAT64", expense_input.amount),
            bigquery.ScalarQueryParameter("date", "DATE", expense_input.date),
            bigquery.ScalarQueryParameter("category", "STRING", expense_input.category),
            bigquery.ScalarQueryParameter("vendor", "STRING", expense_input.vendor),
            bigquery.ScalarQueryParameter("description", "STRING", expense_input.description)
        ]
    )

    try:
        results = bq.query(query, job_config=job_config).result()
        return {
            "message": "Expense record updated successfully",
            "expense_id": expense_input.expense_id,
            "updated_data": expense_input
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )