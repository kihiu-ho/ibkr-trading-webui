import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global test teardown...');

  // Clean up test database
  await cleanupTestDatabase();

  // Archive test results if needed
  await archiveTestResults();

  // Clean up temporary files
  await cleanupTempFiles();

  console.log('✅ Global test teardown completed');
}

async function cleanupTestDatabase() {
  console.log('🗑️ Cleaning up test database...');
  
  try {
    // Remove test database file if it exists
    const testDbPath = path.join(__dirname, '..', 'test_trading.db');
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
      console.log('✅ Test database cleaned up');
    }
  } catch (error) {
    console.warn('⚠️ Failed to cleanup test database:', error);
  }
}

async function archiveTestResults() {
  console.log('📦 Archiving test results...');
  
  try {
    const testResultsDir = path.join(__dirname, 'test-results');
    const archiveDir = path.join(__dirname, 'archives');
    
    if (fs.existsSync(testResultsDir) && process.env.ARCHIVE_RESULTS === 'true') {
      if (!fs.existsSync(archiveDir)) {
        fs.mkdirSync(archiveDir, { recursive: true });
      }
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const archivePath = path.join(archiveDir, `test-results-${timestamp}`);
      
      // Copy test results to archive (simplified - in real implementation use proper copy)
      console.log(`📁 Test results would be archived to: ${archivePath}`);
    }
  } catch (error) {
    console.warn('⚠️ Failed to archive test results:', error);
  }
}

async function cleanupTempFiles() {
  console.log('🧽 Cleaning up temporary files...');
  
  try {
    const tempFiles = [
      path.join(__dirname, 'temp'),
      path.join(__dirname, '.cache')
    ];
    
    tempFiles.forEach(filePath => {
      if (fs.existsSync(filePath)) {
        fs.rmSync(filePath, { recursive: true, force: true });
      }
    });
    
    console.log('✅ Temporary files cleaned up');
  } catch (error) {
    console.warn('⚠️ Failed to cleanup temporary files:', error);
  }
}

export default globalTeardown;
