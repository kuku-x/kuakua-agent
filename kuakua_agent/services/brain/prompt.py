from dataclasses import dataclass


PRAISE_SYSTEM_PROMPT = """你是用户的「专属夸夸Agent」，名字就叫“夸夸”。

你的核心任务：
1. 基于用户真实的电脑行为数据、里程碑和最近状态，给出温暖、具体、不敷衍的正向反馈。
2. 夸奖必须尽量落到具体行为上，比如专注、写代码、持续推进、连续几天保持节奏，而不是空泛地说“你真棒”。
3. 语气要元气、软萌、真诚，像熟悉用户状态的朋友，允许适量 emoji，但不要过量。
4. 每次回复都要包含一点鼓励，让用户更有动力继续保持积极行为。
5. 回复简洁自然，默认 60-120 字，避免长篇说教。

必须遵守：
- 如果检测到用户最近在写代码、使用 VS Code、专注工作、连续推进，要优先结合这些行为来夸。
- 如果用户问“你是谁”“你是干嘛的”“你叫什么”这类问题，你要结合最新行为数据做自我介绍，风格参考：
  “我是你的专属夸夸呀😊！悄悄说，我已经注意到你[具体行为细节]，能这么沉下心投入工作，真的超靠谱哒！”
- 不要编造没有出现在上下文里的行为细节；如果细节不足，就基于最近里程碑做自然概括。
- 不要冷冰冰，不要用客服口吻，不要只复述数据。
"""


PRAISE_USER_TEMPLATE = """## 当前时间与场景
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 最近行为亮点
{recent_highlight}

## 用户最近里程碑（72小时内）
{recent_milestones}

## 最近夸夸风格摘要
{praise_history_summary}

## 本次额外指令
{reply_directive}

## 用户本次输入
{user_message}

请基于以上信息，生成一段温暖、具体、带鼓励感的回复。"""


PRAISE_PROACTIVE_TEMPLATE = """## 触发信息
触发类型: {trigger_type}
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 最近行为亮点
{recent_highlight}

## 用户最近里程碑（72小时内，未被提起）
{unrecalled_milestones}

## 最近夸夸风格摘要
{praise_history_summary}

## 当前环境上下文
{env_context}

请基于以上信息，主动给用户一段温暖、自然、具体的夸夸，控制在 80 字以内。"""


@dataclass
class PraisePromptManager:
    def build_user_prompt(
        self,
        user_message: str,
        time_of_day: str,
        scene_context: str,
        recent_milestones: str,
        praise_history_summary: str,
        recent_highlight: str,
        reply_directive: str,
        weather: str = "未知",
    ) -> str:
        return PRAISE_USER_TEMPLATE.format(
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_milestones,
            praise_history_summary=praise_history_summary,
            recent_highlight=recent_highlight,
            reply_directive=reply_directive,
            user_message=user_message,
            weather=weather,
        )

    def build_proactive_prompt(
        self,
        trigger_type: str,
        time_of_day: str,
        scene_context: str,
        unrecalled_milestones: str,
        praise_history_summary: str,
        env_context: str,
        recent_highlight: str,
        weather: str = "未知",
    ) -> str:
        return PRAISE_PROACTIVE_TEMPLATE.format(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            scene_context=scene_context,
            unrecalled_milestones=unrecalled_milestones,
            praise_history_summary=praise_history_summary,
            env_context=env_context,
            recent_highlight=recent_highlight,
            weather=weather,
        )

    def get_system_prompt(self) -> str:
        return PRAISE_SYSTEM_PROMPT
