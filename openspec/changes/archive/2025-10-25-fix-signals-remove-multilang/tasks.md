# Implementation Tasks

## 1. Fix Chart Generation
- [x] 1.1 Fix IBKRService to support symbol-based data fetching
- [x] 1.2 Add symbol-to-conid lookup in chart generator
- [x] 1.3 Fix data format conversion to DataFrame
- [x] 1.4 Add proper error handling for missing data

## 2. Remove Multi-Language Support
- [x] 2.1 Remove Chinese prompts from LLM service
- [x] 2.2 Remove language parameter from signal generator
- [x] 2.3 Remove language config from settings
- [x] 2.4 Update API to remove language parameter
- [x] 2.5 Update frontend to remove language selector
- [x] 2.6 Update database migration to remove language field

## 3. Simplify Code
- [x] 3.1 Remove language-related conditionals
- [x] 3.2 Update documentation
- [x] 3.3 Update tests

## 4. Fix MinIO Upload Method
- [x] 4.1 Fix chart_generator to use correct MinIO method
- [x] 4.2 Use upload_chart() instead of upload_file()
- [x] 4.3 Fix method signature to match MinIOService
