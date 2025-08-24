#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn } = require('cross-spawn');
const chalk = require('chalk');

console.log(chalk.blue.bold('🤖 ddddocr MCP Server Post-Install'));
console.log(chalk.gray('Setting up CAPTCHA recognition service...\n'));

/**
 * 复制Python文件到正确位置
 */
function copyPythonFiles() {
  try {
    const pythonDir = path.join(__dirname, '..', 'python');
    
    // 创建python目录
    if (!fs.existsSync(pythonDir)) {
      fs.mkdirSync(pythonDir, { recursive: true });
    }
    
    // 需要复制的文件列表
    const filesToCopy = [
      'server.py',
      'config.yaml',
      'requirements.txt'
    ];
    
    const rootDir = path.join(__dirname, '..');
    
    filesToCopy.forEach(file => {
      const srcPath = path.join(rootDir, file);
      const destPath = path.join(pythonDir, file);
      
      if (fs.existsSync(srcPath)) {
        fs.copyFileSync(srcPath, destPath);
        console.log(chalk.green('✅ Copied:'), file);
      } else {
        console.log(chalk.yellow('⚠️  Not found:'), file);
      }
    });
    
    console.log(chalk.green('✅ Python files copied to python/ directory'));
  } catch (error) {
    console.error(chalk.red('❌ Error copying Python files:'), error.message);
  }
}

/**
 * 设置可执行权限（Unix系统）
 */
function setExecutablePermissions() {
  if (process.platform !== 'win32') {
    try {
      const cliPath = path.join(__dirname, '..', 'bin', 'cli.js');
      if (fs.existsSync(cliPath)) {
        fs.chmodSync(cliPath, '755');
        console.log(chalk.green('✅ Set executable permissions for CLI'));
      }
    } catch (error) {
      console.error(chalk.yellow('⚠️  Could not set executable permissions:'), error.message);
    }
  }
}

/**
 * 检查系统要求
 */
function checkSystemRequirements() {
  console.log(chalk.blue('🔍 Checking system requirements...'));
  
  // 检查Node.js版本
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
  
  if (majorVersion >= 14) {
    console.log(chalk.green('✅ Node.js:'), nodeVersion);
  } else {
    console.log(chalk.red('❌ Node.js:'), nodeVersion, '(requires >= 14.0.0)');
  }
  
  // 检查Python（可选）
  try {
    const pythonCheck = spawn.sync('python3', ['--version'], { encoding: 'utf8' });
    if (pythonCheck.status === 0) {
      console.log(chalk.green('✅ Python3:'), pythonCheck.stdout.trim());
    } else {
      const pythonCheck2 = spawn.sync('python', ['--version'], { encoding: 'utf8' });
      if (pythonCheck2.status === 0 && pythonCheck2.stdout.includes('Python 3.')) {
        console.log(chalk.green('✅ Python:'), pythonCheck2.stdout.trim());
      } else {
        console.log(chalk.yellow('⚠️  Python 3.10+ not found. Install it for full functionality.'));
      }
    }
  } catch (error) {
    console.log(chalk.yellow('⚠️  Python check failed. Install Python 3.10+ for full functionality.'));
  }
}

/**
 * 显示安装完成信息
 */
function showCompletionMessage() {
  console.log(chalk.green.bold('\n🎉 Installation completed!\n'));
  
  console.log(chalk.yellow('Next steps:'));
  console.log('  1. Install Python dependencies: ' + chalk.cyan('ddddocr-mcp install'));
  console.log('  2. Check system status:          ' + chalk.cyan('ddddocr-mcp check'));
  console.log('  3. Start the server:             ' + chalk.cyan('ddddocr-mcp start'));
  console.log('  4. Generate IDE config:          ' + chalk.cyan('ddddocr-mcp config'));
  console.log('');
  
  console.log(chalk.yellow('For help:'));
  console.log('  ' + chalk.cyan('ddddocr-mcp help'));
  console.log('');
  
  console.log(chalk.gray('Documentation: https://github.com/your-org/ddddocr-mcp-server'));
}

// 执行安装步骤
async function runPostInstall() {
  try {
    copyPythonFiles();
    setExecutablePermissions();
    checkSystemRequirements();
    showCompletionMessage();
  } catch (error) {
    console.error(chalk.red('❌ Post-install failed:'), error.message);
    process.exit(1);
  }
}

// 运行安装
runPostInstall();