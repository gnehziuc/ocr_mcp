#!/usr/bin/env node

const { Command } = require('commander');
const chalk = require('chalk');
const path = require('path');
const fs = require('fs');
const MCPCaptchaServer = require('../lib/index');

const program = new Command();

program
  .name('ddddocr-mcp')
  .description('ddddocr MCP Server - CAPTCHA recognition service for Model Context Protocol')
  .version(require('../package.json').version);

// 启动服务器命令
program
  .command('start')
  .description('Start the MCP server')
  .option('-t, --transport <type>', 'Transport type (stdio|sse)', 'stdio')
  .option('-p, --port <number>', 'Port for SSE transport', '8000')
  .option('--python-path <path>', 'Path to Python executable')
  .option('--server-path <path>', 'Path to server.py script')
  .option('--no-check-deps', 'Skip dependency check')
  .action(async (options) => {
    try {
      console.log(chalk.blue.bold('🤖 ddddocr MCP Server'));
      console.log(chalk.gray('CAPTCHA Recognition Service for Model Context Protocol\n'));

      const server = new MCPCaptchaServer({
        transport: options.transport,
        port: parseInt(options.port),
        pythonPath: options.pythonPath,
        serverPath: options.serverPath
      });

      // 检查依赖
      if (options.checkDeps !== false) {
        await server.checkDependencies();
      }

      // 启动服务器
      await server.start();
    } catch (error) {
      console.error(chalk.red('❌ Error:'), error.message);
      process.exit(1);
    }
  });

// 安装依赖命令
program
  .command('install')
  .description('Install Python dependencies')
  .option('--python-path <path>', 'Path to Python executable')
  .action(async (options) => {
    try {
      console.log(chalk.blue('📦 Installing dependencies...'));
      
      const server = new MCPCaptchaServer({
        pythonPath: options.pythonPath
      });
      
      await server.installDependencies();
      console.log(chalk.green('✅ Installation completed'));
    } catch (error) {
      console.error(chalk.red('❌ Installation failed:'), error.message);
      process.exit(1);
    }
  });

// 检查状态命令
program
  .command('check')
  .description('Check system requirements and dependencies')
  .option('--python-path <path>', 'Path to Python executable')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔍 Checking system requirements...\n'));
      
      const server = new MCPCaptchaServer({
        pythonPath: options.pythonPath
      });
      
      // 检查Python
      try {
        const pythonPath = server.findPython();
        console.log(chalk.green('✅ Python:'), pythonPath);
      } catch (error) {
        console.log(chalk.red('❌ Python:'), error.message);
        return;
      }
      
      // 检查服务器脚本
      try {
        const serverPath = server.findServerPath();
        console.log(chalk.green('✅ Server script:'), serverPath);
      } catch (error) {
        console.log(chalk.red('❌ Server script:'), error.message);
        return;
      }
      
      // 检查依赖
      try {
        await server.checkDependencies();
      } catch (error) {
        console.log(chalk.red('❌ Dependencies:'), error.message);
        console.log(chalk.yellow('💡 Run `ddddocr-mcp install` to install dependencies'));
        return;
      }
      
      console.log(chalk.green('\n🎉 All checks passed! Ready to start the server.'));
      console.log(chalk.gray('Run `ddddocr-mcp start` to launch the server.'));
    } catch (error) {
      console.error(chalk.red('❌ Check failed:'), error.message);
      process.exit(1);
    }
  });

// 生成配置命令
program
  .command('config')
  .description('Generate MCP configuration for IDE integration')
  .option('-o, --output <path>', 'Output file path', 'mcp-config.json')
  .option('-t, --transport <type>', 'Transport type (stdio|sse)', 'stdio')
  .option('-p, --port <number>', 'Port for SSE transport', '8000')
  .action((options) => {
    try {
      const config = {
        mcpServers: {
          "ddddocr-captcha": {
            command: "npx",
            args: ["ddddocr-mcp", "start", "--transport", options.transport],
            env: {}
          }
        }
      };
      
      if (options.transport === 'sse') {
        config.mcpServers["ddddocr-captcha"].args.push('--port', options.port);
      }
      
      fs.writeFileSync(options.output, JSON.stringify(config, null, 2));
      console.log(chalk.green('✅ Configuration generated:'), options.output);
      console.log(chalk.gray('Add this configuration to your IDE MCP settings.'));
    } catch (error) {
      console.error(chalk.red('❌ Failed to generate config:'), error.message);
      process.exit(1);
    }
  });

// 测试命令
program
  .command('test')
  .description('Test the CAPTCHA recognition functionality')
  .option('-i, --image <path>', 'Path to test image')
  .option('--create-test', 'Create a test image')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🧪 Testing CAPTCHA recognition...'));
      
      // 这里可以添加测试逻辑
      if (options.createTest) {
        console.log(chalk.yellow('💡 Test functionality not implemented yet.'));
        console.log(chalk.gray('Use the Python test client: python test_client.py --create-test'));
      } else {
        console.log(chalk.yellow('💡 Image testing not implemented yet.'));
        console.log(chalk.gray('Use the Python test client for full testing.'));
      }
    } catch (error) {
      console.error(chalk.red('❌ Test failed:'), error.message);
      process.exit(1);
    }
  });

// 显示帮助信息
program
  .command('help')
  .description('Show detailed help information')
  .action(() => {
    console.log(chalk.blue.bold('🤖 ddddocr MCP Server Help\n'));
    
    console.log(chalk.yellow('Quick Start:'));
    console.log('  1. Install dependencies: ' + chalk.cyan('ddddocr-mcp install'));
    console.log('  2. Check system:         ' + chalk.cyan('ddddocr-mcp check'));
    console.log('  3. Start server:         ' + chalk.cyan('ddddocr-mcp start'));
    console.log('');
    
    console.log(chalk.yellow('IDE Integration:'));
    console.log('  1. Generate config:      ' + chalk.cyan('ddddocr-mcp config'));
    console.log('  2. Add to IDE settings:  Copy mcp-config.json content');
    console.log('');
    
    console.log(chalk.yellow('Transport Modes:'));
    console.log('  • stdio: For IDE integration (default)');
    console.log('  • sse:   For web service deployment');
    console.log('');
    
    console.log(chalk.yellow('Examples:'));
    console.log('  ' + chalk.cyan('ddddocr-mcp start --transport sse --port 3000'));
    console.log('  ' + chalk.cyan('ddddocr-mcp config --transport sse --port 3000'));
    console.log('');
    
    console.log(chalk.gray('For more information, visit: https://github.com/your-org/ddddocr-mcp-server'));
  });

// 解析命令行参数
program.parse();

// 如果没有提供命令，显示帮助
if (!process.argv.slice(2).length) {
  program.outputHelp();
}