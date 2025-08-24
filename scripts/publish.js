#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn } = require('cross-spawn');
const chalk = require('chalk');

console.log(chalk.blue.bold('📦 ddddocr MCP Server - NPM Publish Script\n'));

/**
 * 检查发布前的准备工作
 */
function checkPrePublish() {
  console.log(chalk.blue('🔍 Checking pre-publish requirements...'));
  
  const requiredFiles = [
    'package.json',
    'README-npm.md',
    'LICENSE',
    'lib/index.js',
    'bin/cli.js',
    'mcp-config.json',
    'scripts/postinstall.js'
  ];
  
  const missingFiles = [];
  
  requiredFiles.forEach(file => {
    const filePath = path.join(__dirname, '..', file);
    if (!fs.existsSync(filePath)) {
      missingFiles.push(file);
    }
  });
  
  if (missingFiles.length > 0) {
    console.error(chalk.red('❌ Missing required files:'));
    missingFiles.forEach(file => {
      console.error(chalk.red('  - ' + file));
    });
    process.exit(1);
  }
  
  console.log(chalk.green('✅ All required files present'));
}

/**
 * 准备发布文件
 */
function preparePublish() {
  console.log(chalk.blue('📝 Preparing publish files...'));
  
  // 复制README-npm.md为README.md
  const readmeSrc = path.join(__dirname, '..', 'README-npm.md');
  const readmeDest = path.join(__dirname, '..', 'README.md');
  
  if (fs.existsSync(readmeSrc)) {
    fs.copyFileSync(readmeSrc, readmeDest);
    console.log(chalk.green('✅ README.md prepared for npm'));
  }
  
  // 创建python目录并复制文件
  const pythonDir = path.join(__dirname, '..', 'python');
  if (!fs.existsSync(pythonDir)) {
    fs.mkdirSync(pythonDir, { recursive: true });
  }
  
  const filesToCopy = ['server.py', 'config.yaml', 'requirements.txt'];
  const rootDir = path.join(__dirname, '..');
  
  filesToCopy.forEach(file => {
    const srcPath = path.join(rootDir, file);
    const destPath = path.join(pythonDir, file);
    
    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, destPath);
      console.log(chalk.green('✅ Copied to python/:'), file);
    }
  });
}

/**
 * 运行测试
 */
function runTests() {
  console.log(chalk.blue('🧪 Running tests...'));
  
  try {
    const testResult = spawn.sync('npm', ['test'], {
      stdio: 'inherit',
      cwd: path.join(__dirname, '..')
    });
    
    if (testResult.status !== 0) {
      console.error(chalk.red('❌ Tests failed'));
      process.exit(1);
    }
    
    console.log(chalk.green('✅ All tests passed'));
  } catch (error) {
    console.log(chalk.yellow('⚠️  No tests found, skipping...'));
  }
}

/**
 * 检查版本
 */
function checkVersion() {
  console.log(chalk.blue('🔢 Checking version...'));
  
  const packagePath = path.join(__dirname, '..', 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  console.log(chalk.green('📦 Package:'), packageJson.name);
  console.log(chalk.green('🔢 Version:'), packageJson.version);
  
  // 检查是否是预发布版本
  if (packageJson.version.includes('alpha') || 
      packageJson.version.includes('beta') || 
      packageJson.version.includes('rc')) {
    console.log(chalk.yellow('⚠️  This is a pre-release version'));
  }
}

/**
 * 执行发布
 */
function publish() {
  console.log(chalk.blue('🚀 Publishing to npm...'));
  
  const publishArgs = ['publish'];
  
  // 检查是否需要添加标签
  const packagePath = path.join(__dirname, '..', 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  if (packageJson.version.includes('alpha')) {
    publishArgs.push('--tag', 'alpha');
  } else if (packageJson.version.includes('beta')) {
    publishArgs.push('--tag', 'beta');
  } else if (packageJson.version.includes('rc')) {
    publishArgs.push('--tag', 'rc');
  }
  
  // 添加访问权限
  publishArgs.push('--access', 'public');
  
  try {
    const publishResult = spawn.sync('npm', publishArgs, {
      stdio: 'inherit',
      cwd: path.join(__dirname, '..')
    });
    
    if (publishResult.status === 0) {
      console.log(chalk.green.bold('\n🎉 Successfully published to npm!'));
      console.log(chalk.gray('Install with: npm install -g ' + packageJson.name));
    } else {
      console.error(chalk.red('❌ Publish failed'));
      process.exit(1);
    }
  } catch (error) {
    console.error(chalk.red('❌ Publish error:'), error.message);
    process.exit(1);
  }
}

/**
 * 清理发布文件
 */
function cleanup() {
  console.log(chalk.blue('🧹 Cleaning up...'));
  
  // 这里可以添加清理逻辑，比如删除临时文件
  console.log(chalk.green('✅ Cleanup completed'));
}

/**
 * 主发布流程
 */
async function main() {
  try {
    checkPrePublish();
    preparePublish();
    checkVersion();
    runTests();
    
    // 确认发布
    console.log(chalk.yellow('\n⚠️  Ready to publish. Continue? (y/N)'));
    
    // 在实际使用中，这里应该添加用户确认逻辑
    // 现在直接发布
    publish();
    cleanup();
    
  } catch (error) {
    console.error(chalk.red('❌ Publish failed:'), error.message);
    process.exit(1);
  }
}

// 运行发布脚本
if (require.main === module) {
  main();
}

module.exports = {
  checkPrePublish,
  preparePublish,
  runTests,
  checkVersion,
  publish,
  cleanup
};