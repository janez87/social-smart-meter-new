# Social Smart Meter (data processing pipeline)

1. Install requirements.txt.

2. Make sure to add the code/weights and code/models directories to your repository.

2. Edit config.py (fill in access tokens, etc.).

3. Setup (Mongo)DB connection.

4. Run code/collection/data_crawler.py script, which has multiple arguments (source, city, neighborhood, year, month, day). For instance:

```
data_crawler.py instagram amsterdam west 2018 9 23  
```

5. Run code/enrichment/data_enrichment.py script, which has multiple arguments (source, city). For instance:

```
data_enrichment.py instagram amsterdam
```

6. Run code/classification/data_classification.py script, which has one argument (source). For instance:

```
data_classification.py instagram
```
