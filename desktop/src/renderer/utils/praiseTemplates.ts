export const TEMPLATE_PRAISES = [
  "今天也在努力呢，休息一下也没关系哦~",
  "你已经走了很远，给自己点个赞吧",
  "每一天的小进步，都值得被看见",
  "累了就休息，夸夸一直陪着你",
  "相信你已经在最好的路上",
  "不必和别人比较，今天的你比昨天更棒",
  "努力本身就已经很了不起",
  "给自己一首歌的时间放松一下吧",
  "你已经坚持了很久，这本身就很伟大",
  "相信直觉，你做的选择不会错",
  "今天有什么小成就吗？我想听听",
  "记得喝水，记得休息，记得对自己好",
  "你今天也辛苦了",
  "有时候停下脚步，也是前进的一部分",
  "我看见你的努力了，真棒",
]

export function getRandomTemplatePraise(): string {
  return TEMPLATE_PRAISES[Math.floor(Math.random() * TEMPLATE_PRAISES.length)]
}