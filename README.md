# Motivate Me
An AI-powered motivational companion designed to uplift and inspire you. To run the app, click here (note you will need a Snowflake account to log in): https://app.snowflake.com/east-us-2.azure/dea96167/#/streamlit-apps/MOTIVATE_ME_DB.APP_DATA.OZSVM67Z2QLBRDKZ?ref=snowsight_shared

This is a Streamlit-based application that serves as your personal motivational assistant, powered by Snowflake Cortex AI. The app generates motivational messages tailored to your needs, offering three styles:

- **Enthusiastic Hype Man**
- **Warm Encourager**
- **Stoic Performer**

## Features

- **Dynamic Motivational Messages**: Personalized based on user input.
- **Powered by AI**: Utilizes Snowflake Cortex AI + Mistral models for contextual insights.
- **Interactive UI**: Simple and engaging interface built with Streamlit.

## Getting Started

This guide will walk you through setting up your own instance of the application using Snowflake and Streamlit. By following these steps, you'll be able to create a database, schema, and tables in Snowflake, upload the necessary data, and run the Streamlit app to generate personalized motivational messages. 

*Please note: This documentation borrows HEAVILY from the Snowflake RAG Tutorial here: https://quickstarts.snowflake.com/guide/ask_questions_to_your_own_documents_with_snowflake_cortex_search/index.html#1. Please refer to that if you encounter errors in this setup.

Prerequisites:

Before you begin, ensure you have the following:

**Snowflake Account: Access to a Snowflake account where you can create databases and schemas.
**Data Files: A zip file named motivate_me_data.zip (located in this repo) containing the documents to be uploaded.

### Step 1: Set Up Snowflake Environment

#### Create a SQL worksheet
Log in to your Snowflake account and in the top left, create a SQL worksheet. More instructions here: https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-in-sf-web-interface

#### Create a Database:

Execute the following command to create a new database:

```CREATE DATABASE IF NOT EXISTS MOTIVATE_ME_DB;```

#### Create a Schema:

Within the newly created database, create a schema:

```
USE DATABASE MOTIVATE_ME_DB;
CREATE SCHEMA IF NOT EXISTS APP_DATA;
```

#### Create a Table:

Create a table to store the data. 

Create a function to split the text into chunks. Run this in the SQL worksheet.

```
create or replace function text_chunker(pdf_text string)
returns table (chunk varchar)
language python
runtime_version = '3.9'
handler = 'text_chunker'
packages = ('snowflake-snowpark-python', 'langchain')
as
$$
from snowflake.snowpark.types import StringType, StructField, StructType
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

class text_chunker:

    def process(self, pdf_text: str):
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1512, #Adjust this as you see fit
            chunk_overlap  = 256, #This let's text have some form of overlap. Useful for keeping chunks contextual
            length_function = len
        )
    
        chunks = text_splitter.split_text(pdf_text)
        df = pd.DataFrame(chunks, columns=['chunks'])
        
        yield from df.itertuples(index=False, name=None)
$$;
```

Create a Stage with Directory Table where you will be uploading your documents:
```
create or replace stage docs ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE') DIRECTORY = ( ENABLE = true );
```

### Step 2: Upload Data to Snowflake

#### Unzip Data Files:

Extract the contents of motivate_me_data.zip to a local directory.

#### Open the Upload Location

**In Snowflake, click "Data->Databases" in the left sidebar. 
**Then click on the MOTIVATE_ME_DB->APP_DATA->STAGES->DOCS. 

#### Upload the Files:

**On this page, click "+ Files" in the top right.
**Upload the files.

### Step 3: Create the table to store chunks
Run the following in the SQL worksheet:
```
create or replace TABLE DOCS_CHUNKS_TABLE ( 
    RELATIVE_PATH VARCHAR(16777216), -- Relative path to the PDF file
    SIZE NUMBER(38,0), -- Size of the PDF
    FILE_URL VARCHAR(16777216), -- URL for the PDF
    SCOPED_FILE_URL VARCHAR(16777216), -- Scoped url (you can choose which one to keep depending on your use case)
    CHUNK VARCHAR(16777216), -- Piece of text
    CATEGORY VARCHAR(16777216) -- Will hold the document category to enable filtering
);
```

Then run:
```
insert into docs_chunks_table (relative_path, size, file_url,
                            scoped_file_url, chunk)

    select relative_path, 
            size,
            file_url, 
            build_scoped_file_url(@docs, relative_path) as scoped_file_url,
            func.chunk as chunk
    from 
        directory(@docs),
        TABLE(text_chunker (TO_VARCHAR(SNOWFLAKE.CORTEX.PARSE_DOCUMENT(@docs, 
                              relative_path, {'mode': 'LAYOUT'})))) as func;
```

### Step 4: Create Cortex Search Service
Run:
```
create or replace CORTEX SEARCH SERVICE CC_SEARCH_SERVICE_CS
ON chunk
ATTRIBUTES category
warehouse = COMPUTE_WH
TARGET_LAG = '1 minute'
as (
    select chunk,
        relative_path,
        file_url,
        category
    from docs_chunks_table
);
```

### Step 5: Create the Streamlit app

**Click on the streamlit tab on the left.
**Click on + Streamlit App button on the right
**Give the App a name (like "Motivate Me!")
**Select the warehouse to run the App (a Small WH will be enough)
**Choose the MOTIVATE_ME_DB database and APP_DATA schema

### Step 6: Add the code and run!

**In the streamlit app edit window, paste the code in "app.py" (Note: you may need to add the packages in the package manager on screen)
**Run the app! Follow the instructions below or on-screen.

### Usage

1. Enter your name, a challenge you're facing, and an accomplishment you're proud of.
2. Choose your motivational style: Enthusiastic Hype Man, Warm Encourager, or Stoic Performer.
3. Click **Hype me up!** and get your personalized motivational message.

## License

This project is licensed under the MIT License.

