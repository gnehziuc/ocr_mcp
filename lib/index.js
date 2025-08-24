#!/usr/bin/env node

const { spawn } = require('cross-spawn');
const path = require('path');
const fs = require('fs');
const which = require('which');
const chalk = require('chalk');

class MCPCaptchaServer {
  constructor(options = {}) {
    this.options = {
      transport: 'stdio',
      port: 8000,
      pythonPath: null,
      serverPath: null,
      ...options
    };
    this.serverProcess = null;
  }

  /**
   * 查找Python可执行文件
   */
  findPython() {
    if (this.options.pythonPath) {
      return this.options.pythonPath;
    }

    // 优先使用系统Python，避免使用虚拟环境
    const pythonCommands = process.platform === 'win32' 
      ? ['py', 'python', 'python3']
      : ['python3', 'python', 'py'];
    
    for (const cmd of pythonCommands) {
      try {
        const pythonPath = which.sync(cmd);
        
        // 跳过虚拟环境中的Python
        const lowerPath = pythonPath.toLowerCase();
        if (lowerPath.includes('venv') || 
            lowerPath.includes('virtualenv') || 
            lowerPath.includes('.env') ||
            lowerPath.includes('scripts') ||
            lowerPath.includes('site-packages') ||
            lowerPath.includes('conda') ||
            lowerPath.includes('miniconda') ||
            lowerPath.includes('anaconda')) {
          // Skip virtual environment Python silently
          continue;
        }
        
        // 验证Python版本
        const versionCheck = spawn.sync(pythonPath, ['--version'], { encoding: 'utf8' });
        if (versionCheck.stdout && versionCheck.stdout.includes('Python 3.')) {
          const version = versionCheck.stdout.trim();
          // Found system Python
          return pythonPath;
        }
      } catch (error) {
        continue;
      }
    }

    throw new Error('Python 3.x not found. Please install Python 3.10+ or specify pythonPath option.');
  }

  /**
   * 查找服务器脚本路径
   */
  findServerPath() {
    if (this.options.serverPath) {
      return this.options.serverPath;
    }

    // 查找可能的服务器路径
    const possiblePaths = [
      path.join(__dirname, '..', 'python', 'server.py'),
      path.join(__dirname, '..', 'server.py'),
      path.join(process.cwd(), 'server.py')
    ];

    for (const serverPath of possiblePaths) {
      if (fs.existsSync(serverPath)) {
        return serverPath;
      }
    }

    throw new Error('MCP server script not found. Please ensure server.py is available.');
  }

  /**
   * 启动MCP服务器
   */
  async start() {
    try {
      const pythonPath = this.findPython();
      const serverPath = this.findServerPath();

      console.log(chalk.blue('🚀 Starting ddddocr MCP Server...'));
      console.log(chalk.gray(`Python: ${pythonPath}`));
      console.log(chalk.gray(`Server: ${serverPath}`));
      console.log(chalk.gray(`Transport: ${this.options.transport}`));

      const args = [serverPath];
      
      // 添加传输方式参数
      if (this.options.transport === 'sse') {
        args.push('--transport', 'sse', '--port', this.options.port.toString());
      }

      // 启动Python服务器
      this.serverProcess = spawn(pythonPath, args, {
        stdio: this.options.transport === 'stdio' ? 'inherit' : 'pipe',
        env: { ...process.env }
      });

      // 处理服务器进程事件
      this.serverProcess.on('error', (error) => {
        console.error(chalk.red('❌ Failed to start server:'), error.message);
        process.exit(1);
      });

      this.serverProcess.on('exit', (code, signal) => {
        if (code !== 0) {
          console.error(chalk.red(`❌ Server exited with code ${code}`));
          process.exit(code || 1);
        }
      });

      // SSE模式下显示服务器URL
      if (this.options.transport === 'sse') {
        console.log(chalk.green(`✅ Server started at http://localhost:${this.options.port}`));
        
        // 监听服务器输出
        this.serverProcess.stdout.on('data', (data) => {
          console.log(data.toString());
        });
        
        this.serverProcess.stderr.on('data', (data) => {
          console.error(data.toString());
        });
      } else {
        console.log(chalk.green('✅ Server started in stdio mode'));
      }

      // 处理进程退出
      process.on('SIGINT', () => this.stop());
      process.on('SIGTERM', () => this.stop());

      return this.serverProcess;
    } catch (error) {
      console.error(chalk.red('❌ Error starting server:'), error.message);
      throw error;
    }
  }

  /**
   * 停止MCP服务器
   */
  stop() {
    if (this.serverProcess) {
      console.log(chalk.yellow('🛑 Stopping server...'));
      this.serverProcess.kill('SIGTERM');
      this.serverProcess = null;
    }
  }

  /**
   * 检查依赖是否已安装
   */
  async checkDependencies() {
    try {
      const pythonPath = this.findPython();
      
      // 检查Python包依赖
      const checkCmd = spawn.sync(pythonPath, ['-c', 'import mcp, ddddocr, yaml'], {
        encoding: 'utf8',
        stdio: 'pipe'
      });

      if (checkCmd.status !== 0) {
        console.log(chalk.yellow('⚠️  Python dependencies not found. Installing...'));
        await this.installDependencies();
      } else {
        console.log(chalk.green('✅ Python dependencies are installed'));
      }
    } catch (error) {
      console.error(chalk.red('❌ Error checking dependencies:'), error.message);
      throw error;
    }
  }

  /**
   * 安装Python依赖
   */
  async installDependencies() {
    try {
      // 强制使用系统Python安装依赖，避免虚拟环境干扰
      let pythonPath = this.findPython();
      
      // 在Windows上，如果检测到虚拟环境激活，强制使用系统Python
      if (process.platform === 'win32' && process.env.VIRTUAL_ENV) {
        const systemPythonPaths = [
          'C:\\Windows\\py.EXE',
          'C:\\Python\\python.exe',
          'python'
        ];
        
        for (const sysPath of systemPythonPaths) {
          try {
            const resolvedPath = which.sync(sysPath);
            // 确保不是虚拟环境中的Python
            if (!resolvedPath.toLowerCase().includes('venv') && 
                !resolvedPath.toLowerCase().includes('virtualenv') &&
                !resolvedPath.toLowerCase().includes('.env')) {
              pythonPath = resolvedPath;
              break;
            }
          } catch (e) {
            // 继续尝试下一个路径
          }
        }
      }
      
      if (!pythonPath) {
        throw new Error('Python not found');
      }

      // 查找requirements.txt文件的可能位置
      const possibleRequirementsPath = [
        path.join(__dirname, '..', 'python', 'requirements.txt'),  // npm包中的位置
        path.join(__dirname, '..', 'requirements.txt'),             // 项目根目录
        path.join(process.cwd(), 'requirements.txt')                // 当前工作目录
      ];
      
      let requirementsPath = null;
      for (const reqPath of possibleRequirementsPath) {
        if (fs.existsSync(reqPath)) {
          requirementsPath = reqPath;
          break;
        }
      }
      
      if (!requirementsPath) {
        throw new Error('requirements.txt not found in any expected location');
      }
      
      // Installing Python dependencies silently
      
      const installProcess = spawn(pythonPath, ['-m', 'pip', 'install', '-r', requirementsPath], {
        stdio: 'inherit'
      });

      return new Promise((resolve, reject) => {
        installProcess.on('exit', (code) => {
          if (code === 0) {
            // Dependencies installed successfully
            resolve();
          } else {
            reject(new Error(`pip install failed with code ${code}`));
          }
        });

        installProcess.on('error', reject);
      });
    } catch (error) {
      console.error(chalk.red('❌ Error installing dependencies:'), error.message);
      throw error;
    }
  }
}

module.exports = MCPCaptchaServer;

// 如果直接运行此文件
if (require.main === module) {
  const server = new MCPCaptchaServer();
  server.checkDependencies()
    .then(() => server.start())
    .catch((error) => {
      console.error(chalk.red('❌ Failed to start server:'), error.message);
      process.exit(1);
    });
}