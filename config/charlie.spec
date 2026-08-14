# -*- mode: python ; coding: utf-8 -*-
"""
Charlie 语音助手 — PyInstaller spec 文件（适配 src/ 重组结构）

构建命令（在项目根目录执行）:
    pyinstaller config/charlie.spec --distpath dist --workpath build

输出:
    dist/charlie/            # 目录模式 (启动快, 体积小)
    dist/charlie/charlie     # 可执行文件 (macOS/Linux)
    dist/charlie/charlie.exe # 可执行文件 (Windows)
"""
import os
import sys
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录（spec 在 config/ 下，根目录是上一级）
# PyInstaller exec() 上下文中 __file__ 不可用，通过 CHRL_ROOT 环境变量传入
ROOT = os.environ.get("CHRL_ROOT", os.path.dirname(os.getcwd()))
SRC = os.path.join(ROOT, "src")
os.chdir(ROOT)  # PyInstaller 在项目根运行，datas 相对路径以此为基准

# 收集所有隐式依赖的 Python 包
hidden_imports = [
    # MCP 子进程模块
    'skills.mcp_ir_control', 'skills.mcp_common',
    'integrations.baize_skills_mcp', 'integrations.tuya_api',
    'integrations.tuya_proxy', 'integrations.personalized_push',
    'app.audio', 'app.brain_health', 'app.state',
    'app.reminders', 'app.config', 'app.env_catalog', 'app.preflight',
    'app.cert', 'app.mcp_gate', 'utils',
    # qwen_agent 隐式依赖
    'qwen_agent', 'qwen_agent.agents', 'qwen_agent.tools',
    'qwen_agent.tools.mcp_manager',
    # mcp SDK
    'mcp', 'mcp.server.fastmcp', 'mcp.client.stdio',
    'mcp.client.sse', 'mcp.client.streamable_http',
    'soundfile',
    # ASR/TTS
    'requests', 'urllib3',
    # 音频处理
    'audioop',
    # Web框架
    'uvicorn', 'fastapi', 'starlette', 'sse_starlette',
    'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on',
    # 其他
    'psutil', 'dotenv', 'tiktoken',
    'numpy',
    # 原生桌面窗口 (pywebview + WebView2)
    'webview', 'webview.platforms.edgechromium', 'webview.platforms.winforms',
    'clr', 'pythonnet',
    # 跨平台系统控制/截图(可选，缺失自动降级)
    'mss', 'comtypes', 'pycaw', 'pycaw.pycaw',
    'fcntl_compat',
]

# 收集数据文件（前端 HTML, 模板, 配置）
datas = [
    # 前端静态文件
    (os.path.join(SRC, 'web'), 'web'),
    # app 模块
    (os.path.join(SRC, 'app'), 'app'),
    # agent 模块
    (os.path.join(SRC, 'agent'), 'agent'),
    # skills 模块（MCP 技能，文件名带连字符需作为数据文件打包）
    (os.path.join(SRC, 'skills'), 'skills'),
    # integrations 模块
    (os.path.join(SRC, 'integrations'), 'integrations'),
    # hardware 模块
    (os.path.join(SRC, 'hardware'), 'hardware'),
    # 配置模板
    (os.path.join(ROOT, '.env.example'), '.'),
    # Windows fcntl 垫片
    (os.path.join(SRC, 'fcntl_compat.py'), '.'),
    # 工具脚本
    (os.path.join(ROOT, 'scripts'), 'scripts'),
    # ESP32 干净固件（已擦除 NVS）
    (os.path.join(ROOT, 'dist', 'firmware'), 'firmware'),
]

# 收集隐式依赖的包数据
for pkg in ['qwen_agent', 'mcp', 'fastapi', 'starlette', 'uvicorn', 'sse_starlette', 'webview', 'pythonnet',
            # esptool：应用内 ESP32 烧录向导需要
            'esptool', 'reedsolo', 'serial', 'bitstring', 'intelhex']:
    pkg_data = collect_data_files(pkg)
    datas.extend(pkg_data)
    hidden_imports.extend(collect_submodules(pkg))

# 排除 __pycache__ / .pyc
def _is_cache(src, dest):
    return '__pycache__' in src.replace('\\', '/').split('/') or src.endswith(('.pyc', '.pyo'))
datas = [(s, d) for (s, d) in datas if not _is_cache(s, d) and os.path.exists(s)]

# ffmpeg 二进制文件（从系统查找）
def _find_ffmpeg():
    import shutil
    path = shutil.which('ffmpeg')
    if path:
        return path
    for p in ['/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg',
              '/usr/bin/ffmpeg', '/opt/local/bin/ffmpeg']:
        if os.path.isfile(p):
            return p
    if platform.system() == 'Windows':
        for p in [r'C:\ffmpeg\bin\ffmpeg.exe', r'C:\Program Files\ffmpeg\bin\ffmpeg.exe']:
            if os.path.isfile(p):
                return p
    return None

def _find_ncm():
    import shutil
    path = shutil.which('ncm')
    if path:
        return path
    for p in [os.path.expanduser('~/.local/bin/ncm'), '/usr/local/bin/ncm']:
        if os.path.isfile(p):
            return p
    return None

ffmpeg_path = _find_ffmpeg()
if ffmpeg_path:
    datas.append((ffmpeg_path, 'bin'))
    print(f"[spec] 找到 ffmpeg: {ffmpeg_path}")
else:
    print("[spec] ! 未找到 ffmpeg，音频转码将不可用！")

ncm_path = _find_ncm()
if ncm_path:
    datas.append((ncm_path, 'bin'))
    print(f"[spec] 找到 ncm: {ncm_path}")

binaries = []
if ffmpeg_path:
    binaries.append((ffmpeg_path, 'bin'))
if ncm_path:
    binaries.append((ncm_path, 'bin'))
binaries = [(s, d) for (s, d) in binaries if not _is_cache(s, d)]

a = Analysis(
    [os.path.join(SRC, 'charlie_main.py')],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'pandas',
        'scipy', 'cv2', 'torch', 'tensorflow',
        'tests', 'pytest', 'unittest', 'IPython',
        'jupyter', 'notebook', 'ipykernel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='charlie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['*.pyd', 'pythonnet*', '*pythonnet*', '*WebView2*', '*clr*',
                 'pycaw*', '*pycaw*', 'comtypes*', '*comtypes*'],
    console=False,  # 原生桌面窗口模式
    disable_windowed_traceback=False,
    target_architecture=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, 'config', 'charlie.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['*.pyd', 'pythonnet*', '*WebView2*', 'pycaw*', 'comtypes*'],
    name='charlie',
)
