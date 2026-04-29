from dataclasses import dataclass

from kuakua_agent.config import settings


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

PRAISE_SYSTEM_PROMPT_V2 = """你是本地运行的「夸夸Agent」。

目标：
1. 基于上下文中的真实行为信息给出具体、温暖、短小的鼓励。
2. 不编造上下文里没有的细节；细节不足时做保守概括。
3. 优先强调“已完成的行动”和“可持续的下一步”，避免空泛鸡汤。
4. 默认输出 60-120 字，允许少量 emoji。
"""


PRAISE_USER_TEMPLATE = """## 当前时间与场景
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 最近使用节奏画像（软件使用）
{recent_usage_summary}

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

## 最近使用节奏画像（软件使用）
{recent_usage_summary}

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
    _SYSTEM_PROMPTS = {
        "v1": PRAISE_SYSTEM_PROMPT,
        "v2": PRAISE_SYSTEM_PROMPT_V2,
    }

    def build_user_prompt(
        self,
        user_message: str,
        time_of_day: str,
        scene_context: str,
        recent_milestones: str,
        praise_history_summary: str,
        recent_highlight: str,
        recent_usage_summary: str,
        reply_directive: str,
        weather: str = "未知",
    ) -> str:
        return PRAISE_USER_TEMPLATE.format(
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_milestones,
            praise_history_summary=praise_history_summary,
            recent_highlight=recent_highlight,
            recent_usage_summary=recent_usage_summary,
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
        recent_usage_summary: str,
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
            recent_usage_summary=recent_usage_summary,
            weather=weather,
        )

    def get_system_prompt(self) -> str:
        return self._SYSTEM_PROMPTS.get(settings.praise_prompt_version, PRAISE_SYSTEM_PROMPT)

    def build_fallback_reply(self, recent_highlight: str) -> str:
        highlight = (recent_highlight or "").strip() or "你今天也在认真推进自己的节奏。"
        return f"夸夸在这儿～看到你{highlight}，这份持续投入真的很棒！先给自己点个赞，继续稳稳向前呀 💪"


NIGHTLY_SUMMARY_SYSTEM_PROMPT = """你是用户的「夸夸晚间总结师」。你需要根据用户今天的使用数据，生成一段温暖的晚间总结。

输出要求：
- 分为三个自然段落：「今日回顾」「夸奖时刻」「明日建议」
- 每个段落用中文小标题标出
- 语气温暖真诚，像了解用户状态的亲密朋友
- 基于真实数据给出具体反馈，不要编造
- 总字数控制在 150-250 字
- 允许适量 emoji，每段不超过 1 个

格式示例：
今日回顾
今天你在电脑前累计 X 小时，主要活跃在 XXX。手机端主要看了 XXX，整体节奏偏专注/放松。

夸奖时刻
【基于数据的真诚夸奖，1-2 句】

明日建议
【1-2 条具体可行的建议】
"""

NIGHTLY_SUMMARY_USER_TEMPLATE = """## 今日使用数据

总活跃时长: {total_hours} 小时
工作时长: {work_hours} 小时
娱乐时长: {entertainment_hours} 小时
其他时长: {other_hours} 小时
专注分: {focus_score} / 100

电脑端 Top 应用: {computer_top_apps}
手机端 Top 应用: {phone_top_apps}

数据洞察: {insights}

天气: {weather}

## 最近 7 天趋势
{recent_summary}

请根据以上数据，生成今日晚间总结（包含今日回顾、夸奖时刻、明日建议三个段落）。"""
