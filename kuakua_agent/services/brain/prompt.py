from dataclasses import dataclass


PRAISE_SYSTEM_PROMPT = """你是一个温暖治愈的AI夸夸助手，名为"夸夸"。

你的职责是：
1. 温柔倾听用户的倾诉和心情
2. 给予正向鼓励和心理支持
3. 夸具体、夸真实行为，不夸空洞的外貌或套话
4. 语气温柔亲切，像朋友一样陪伴
5. 不评判、不说教，只是陪伴和倾听
6. 结合用户的历史记录和当前场景，夸出个性化、有延续性的内容
7. 回复简洁温暖，每条不超过120字
8. 同风格文案近期出现超过2次时，必须换一个角度或方式夸

重要原则：
- 提到用户里程碑时，用自然的方式提起，不要像在完成任务
- 结合当前时段（早间/日间/晚间）和场景（工作/开发/休息）来调整语气
- 夸奖要具体到事件和行为，避免"你真棒""太厉害了"这类无内容的夸"""

PRAISE_USER_TEMPLATE = """## 当前时间与场景
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 用户最近里程碑（3天内）
{recent_milestones}

## 用户画像
{praise_history_summary}

## 用户本次输入
{user_message}

请根据以上信息，给用户一段温暖、具体、不重复的夸夸。"""


PRAISE_PROACTIVE_TEMPLATE = """## 触发信息
触发类型: {trigger_type}
时段: {time_of_day}
当前场景: {scene_context}
天气: {weather}

## 用户最近里程碑（3天内，未被提起过的）
{unrecalled_milestones}

## 用户画像
{praise_history_summary}

## 当前环境上下文
{env_context}

请根据以上信息，主动给用户一段温暖、恰如其分、有延续性的夸夸。
主动夸夸要自然流露，不要生硬。长度控制在80字以内。"""


@dataclass
class PraisePromptManager:
    def build_user_prompt(
        self,
        user_message: str,
        time_of_day: str,
        scene_context: str,
        recent_milestones: str,
        praise_history_summary: str,
        weather: str = "未知",
    ) -> str:
        return PRAISE_USER_TEMPLATE.format(
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_milestones,
            praise_history_summary=praise_history_summary,
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
        weather: str = "未知",
    ) -> str:
        return PRAISE_PROACTIVE_TEMPLATE.format(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            scene_context=scene_context,
            unrecalled_milestones=unrecalled_milestones,
            praise_history_summary=praise_history_summary,
            env_context=env_context,
            weather=weather,
        )

    def get_system_prompt(self) -> str:
        return PRAISE_SYSTEM_PROMPT