## 1. Docker Image Updates

- [x] 1.1 Install Chromium in Dockerfile.airflow
- [x] 1.2 Install Chromium-driver in Dockerfile.airflow
- [x] 1.3 Set CHROME_BIN environment variable
- [x] 1.4 Set CHROMIUM_PATH environment variable
- [ ] 1.5 Rebuild Airflow Docker image
- [ ] 1.6 Verify Chromium is installed in container

## 2. Chart Generator Improvements

- [x] 2.1 Add HTML export as fallback in chart_generator.py
- [x] 2.2 Catch ChromeNotFoundError specifically
- [x] 2.3 Initialize Kaleido with Chromium path if available
- [x] 2.4 Improve error messages for Chromium issues
- [x] 2.5 Update ChartResult to support HTML fallback (HTML fallback saves .html file)
- [x] 2.6 Log warnings when using HTML fallback

## 3. Error Handling

- [x] 3.1 Add specific handling for ChromeNotFoundError
- [x] 3.2 Provide clear error messages with installation instructions
- [x] 3.3 Ensure workflow continues even if JPEG export fails
- [ ] 3.4 Update error context in XCom for debugging (optional)

## 4. Testing

- [ ] 4.1 Test chart generation with Chromium installed
- [ ] 4.2 Test HTML fallback when Chromium not available
- [ ] 4.3 Test error handling and messages
- [ ] 4.4 Test end-to-end workflow execution
- [ ] 4.5 Verify charts are generated and stored correctly
- [ ] 4.6 Verify workflow completes successfully

## 5. Validation

- [ ] 5.1 Verify Chromium is accessible in Airflow container
- [ ] 5.2 Verify Kaleido can use Chromium
- [ ] 5.3 Verify charts are generated successfully
- [ ] 5.4 Verify workflow completes without errors
- [ ] 5.5 Verify artifacts are stored correctly

