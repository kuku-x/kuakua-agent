# 本地 TTS 迁移计划 — Kokoro-82M

## 背景

当前夸夸 App 的语音播报依赖 `Fish Audio` 云端 API。

现状问题：

- 晚间总结和主动夸夸的语音能力已经接入，但是否能播出依赖外部账户余额。
- 当前实测返回 `402 Insufficient Balance`，说明 API 链路可达，但免费额度或账户余额不可用。
- 语音播报属于高频、轻量、偏"陪伴型"的能力，不适合长期依赖按次计费云服务。

因此，下一步建议把语音播报迁移到 `本地离线 TTS`。

## 目标

迁移完成后，希望达到：

- 晚间总结可以每天稳定自动播报。
- 主动夸夸可以在不联网、不扣费的情况下播报。
- 本地语音失败时，不影响通知和文本展示。
- 配置路径尽量简单，优先适配 Windows 本机使用场景。

## 推荐方案

首选方案：`Kokoro-82M`

推荐原因：

- **免费、开源** — Apache 2.0 协议，可商用。
- **极轻量** — 仅 82M 参数，CPU 实时推理速度达 3-11 倍实时。
- **中文音色丰富** — v1.1-zh 版本提供 100+ 中文音色（女声 zf_xxx / 男声 zm_xxx），可精挑细选最适合"温柔大姐姐"夸夸场景的声音。
- **Hugging Face TTS Arena 排名第一** — 音质有保障。
- **安装极简** — `pip install kokoro` 一行搞定，依赖轻量。
- **完全本地离线** — 不依赖网络，安全可靠。

暂不优先的方案：

- `CosyVoice-300M-Lite`
  优点是中文效果好，但 Windows 部署烦琐（需 conda + git clone），且中文仅一种女声，不可选音色。
- `edge-tts`
  优点是情感表达好、安装简单，但本质是逆向微软 Edge 内部接口，存在被微软封堵的风险，且需联网。
- `Piper TTS`
  优点是超轻量，但中文音质一般，语调平淡，不适合夸夸场景。
- `Fish Speech` / `Coqui XTTS`
  功能强但部署重，对现阶段来说不划算。

## Kokoro-82M 环境准备指引

### 安装 Kokoro

```bash
pip install kokoro soundfile
```

可选加速（推荐，可提升 CPU 推理速度）：

```bash
pip install onnxruntime
```

### 下载模型和音色

Kokoro v1.1-zh 专门优化了中文，下载方式：

```bash
# 国内推荐使用 ModelScope
pip install modelscope
modelscope download --model AI-ModelScope/Kokoro-82M-v1.1-zh --local_dir ./ckpts/kokoro-v1.1
```

或使用 Hugging Face：

```bash
pip install huggingface-hub
huggingface-cli download hexgrad/Kokoro-82M-v1.1-zh --local-dir ./ckpts/kokoro-v1.1
```

目录结构：

```
./ckpts/kokoro-v1.1/
├── kokoro-v1_1-zh.pth    # 模型权重（~350MB）
├── config.json            # 模型配置
└── voices/                # 音色文件（每个 ~1KB）
    ├── zf_001.pt          # 中文女声音色 1
    ├── zf_002.pt          # 中文女声音色 2
    ├── ...
    └── zm_009.pt          # 中文男声音色
```

### 中文音色推荐列表

推荐几款适合"温柔大姐姐"夸夸场景的女声音色：

| 音色 ID | 风格描述 |
|---------|---------|
| `zf_001` | 标准温柔女声，最常用的中文音色 |
| `zf_002` | 温暖亲切，适合日常陪伴 |
| `zf_003` | 轻柔治愈，适合安慰和鼓励 |
| `zf_018` | 元气可爱，适合活泼夸赞 |
| `zf_032` | 知性沉稳，适合晚间总结 |
| `zf_042` | 甜美软萌，适合日常夸夸 |

可先在 [在线 Demo](https://huggingface.co/spaces/hexgrad/Kokoro-TTS) 试听挑选。

### 验证安装

```python
from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='z')  # 'z' = 中文
generator = pipeline(
    "夸夸在这儿～今天你专注工作了 4 小时，这种投入的状态真让人安心！",
    voice='zf_001',      # 指定音色
    speed=1.0,           # 语速
)
for _, (_, audio) in enumerate(generator):
    sf.write('test.wav', audio, 24000)  # 采样率 24000
    break
```

能正常生成 `test.wav` 即表示安装成功。

### 音频格式注意

Kokoro 默认输出 **24kHz float32 mono** 音频。当前 `FishTTS._play_audio()` 使用 `System.Media.SoundPlayer` 播放 WAV，需要将音频转为 WAV 格式。适配时会在 `_play_audio` 中处理格式转换，或用 `soundfile` 直接写入 WAV。

## 迁移范围

需要改动的主要模块：

- `kuakua_agent/services/output/tts.py`
  当前是 `FishTTS`，迁移为以 `KokoroTTS` 为主的本地实现，并保留必要的播放复用逻辑。
- `kuakua_agent/services/output/__init__.py`
  导出新的本地 TTS 通道。
- `kuakua_agent/services/scheduler/scheduler.py`
  主动夸夸继续走语音通道，但底层换成本地 TTS。
- `kuakua_agent/services/nightly_summary_scheduler.py`
  晚间总结继续走语音通道，但底层换成本地 TTS。
- 设置页
  增加或调整语音引擎配置，至少明确当前使用的是本地引擎。

## 代码接口设计

### KokoroTTS 类骨架

`kuakua_agent/services/output/tts.py` 中新增：

```python
class KokoroTTS(OutputChannel):
    """本地离线 TTS，通过 Kokoro-82M 模型生成语音。"""

    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()
        self._cache_dir = Path(tempfile.gettempdir()) / "kuakua_tts"
        self._pipeline = None  # 延迟加载

    def _get_pipeline(self):
        if self._pipeline is None:
            from kokoro import KPipeline
            self._pipeline = KPipeline(lang_code='z')
        return self._pipeline

    def supports(self, channel_type: str) -> bool:
        return channel_type in ("tts", "voice", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        # 1. 检查 tts_enable 开关
        # 2. 取 kokoro_model_path 和 kokoro_voice
        # 3. 如果模型文件缺失 → OutputResult(success=False, error="Kokoro 模型未配置")
        # 4. 计算缓存 hash → 检查缓存 → 有则直接播放
        # 5. 调用 _generate() 生成 wav
        # 6. 调用 _play_audio() 播放（复用现有实现）
        ...

    def _generate(self, text: str) -> bytes:
        """调用 Kokoro 模型生成音频，返回 WAV bytes。"""
        pipeline = self._get_pipeline()
        voice = self._pref.get("kokoro_voice") or "zf_001"
        speed = self._pref.get_float("tts_speed", 1.0)

        generator = pipeline(text, voice=voice, speed=speed)
        audio_chunks = []
        for _, (_, audio) in enumerate(generator):
            audio_chunks.append(audio)

        import numpy as np
        import soundfile as sf
        import io
        full_audio = np.concatenate(audio_chunks) if len(audio_chunks) > 1 else audio_chunks[0]
        buf = io.BytesIO()
        sf.write(buf, full_audio, 24000, format='WAV')
        return buf.getvalue()
```

### `__init__.py` 更新

```python
from kuakua_agent.services.output.tts import KokoroTTS

__all__ = [
    "OutputChannel", "OutputManager", "OutputResult",
    "SystemNotifier", "KokoroTTS",
]
```

### 调度器接入方式

`scheduler.py` 和 `nightly_summary_scheduler.py` 中：

- 原来：`self._output_mgr.register(FishTTS())`
- 改为：直接注册 `KokoroTTS()`，并保留通知链路作为语音失败时的兜底

## 建议实现方式

### 阶段 1：基础可用版

目标：先让本地语音播报跑起来。

计划内容：

- 新增 `KokoroTTS` 输出通道。
- 内联调用 Kokoro Python 库生成音频。
- 复用当前已有的本地音频播放逻辑（`_play_audio` 通过 `soundfile` 写 WAV 后直接兼容）。
- 晚间总结和主动夸夸都切到本地语音通道。
- 如果本地 TTS 不可用，仍保留文本通知，不让主流程失败。
- **内建基本错误诊断**：模型文件缺失 / 生成失败 / 播放失败，每种场景都返回明确的 `OutputResult.error` 信息，方便用户在设置页看到具体失败原因。

建议配置项：

- `kokoro_model_path`
- `kokoro_voice`
- `tts_speed`

#### 阶段 1 验收标准

以下场景必须逐条通过，才算"基础可用版"完成：

1. **正常播报** — 配置了正确的 `kokoro_model_path` 和 `kokoro_voice` 后，晚间总结自动触发语音播报，能听到语音。
2. **模型文件缺失** — `kokoro_model_path` 指向不存在的文件时，返回明确错误信息，主流程不受影响。
3. **生成失败** — 模型推理失败时，明确错误信息写入 `OutputResult.error`。
4. **tts_enable = false** — 关闭 TTS 开关后，不调用 Kokoro，不报错。
5. **缓存命中** — 同一段文本两次播报，第二次直接从缓存播放，不再调用模型推理。
6. **联网不依赖** — 断网环境下仍然可以正常播报。

### 阶段 2：体验完善版

目标：让用户自己能配置、测试、排错。

计划内容：

- 设置页新增"测试语音播报"按钮。
- 设置页展示本地 TTS 是否已就绪。
- 找不到模型、播放失败时，给出清晰错误信息。
- README 增加本地 TTS 安装说明。

### 阶段 3：体验细化

目标：让 Kokoro 方案更稳定、更贴合陪伴场景。

计划内容：

- 支持切换多个中文音色。
- 允许为晚间总结和主动夸夸选择不同音色。
- 增加更细的音色推荐、试听和缓存管理能力。

## 技术设计建议

### 1. 输出层不要继续写死云服务

建议把现在的 `FishTTS` 迁移为历史实现，把 `KokoroTTS` 作为当前唯一正式 TTS 通道。

可演进为：

- `OutputChannel`
- `KokoroTTS`
- `get_tts_channel()`

这样当前实现更简洁；如果未来真的要重新引入其他 TTS，也只需要在输出层扩展，不必改调度器。

### 2. 调度器层保持不变

主动夸夸和晚间总结这两处，尽量继续只关心：

- 要不要播
- 播什么内容

不要在调度器里耦合具体语音引擎实现，只关心“要不要播”和“播什么”。

### 3. 本地资源路径要显式配置

Windows 下最容易出问题的是：

- 模型文件路径
- 音频缓存路径
- 带空格路径

因此建议不要把 Kokoro 路径写死在代码里，统一走配置。

### 4. 失败策略要温和

语音播报失败时：

- 记录日志
- 保留系统通知
- 保留应用内晚间总结卡片
- 不阻断"已生成晚间总结"的主流程

## 配置迁移方案

### 现有配置项梳理

当前 `PreferenceStore.DEFAULT_PREFS` 中的 TTS 相关键：

| Key | 默认值 | 用途 | 迁移后处理 |
|-----|--------|------|-----------|
| `tts_enable` | `"false"` | TTS 总开关 | **保留**，继续作为 Kokoro 总开关 |
| `tts_voice` | `"default"` | 音色 ID（Fish Audio） | **迁移/废弃**，由 `kokoro_voice` 替代，默认 `zf_001` |
| `tts_speed` | `"1.0"` | 语速 | **保留**，Kokoro 直接支持 |

### 新增配置项

| Key | 默认值 | 用途 |
|-----|--------|------|
| `kokoro_voice` | `"zf_001"` | Kokoro 中文音色 ID |
| `kokoro_model_path` | `./ckpts/kokoro-v1.1` | Kokoro 模型目录或权重所在路径 |
