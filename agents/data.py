import json
import os


class Data:
    """
    Data class for loading data from local files.
    """
    def __init__(self, config):
        self.config = config
        self.users = {}
        self.background = {}
        self.prompt = {}
        self.load_data(config["data_path"])
        self.load_prompt(config["prompt_path"])

    def load_data(self, file_path):
        with open(file_path, "r", encoding='utf-8') as file:
            json_data = json.load(file)
        self.users = json_data

        self.background = {
            # example
            '2': {
                'background': '小明5月有一周的假期，想研究一下能去北京的周边哪些地方旅行。请从花费（包括交通、住宿和娱乐），价值（度假时可以进行那些活动）和方便程度三方面考虑，选择一个合适的旅行目的地。',
                'goal': '请你根据搜索结果，列出你觉得可能可行的备选目的地，并且挑选出你觉得最好的一个地方，说说为什么。',
            },

            # test
            '1': {
                'background': '小明所在的部门刚刚招聘了十个新员工，近期需要进行新员工培训。请查找一个适合新员工培训时采用，大约十人参与的破冰游戏的玩法。',
                'goal': '请你根据搜索结果，讲出给你印象最深的1个破冰游戏的名称，并用一句话描述这个游戏需要做哪些准备？',
            },
            '3': {
                'background': '小明在清华大学附近，想买一辆死飞自行车，请查找可能的购买渠道，注意事项和价格区间。',
                'goal': '请你根据搜索结果，告诉小明应该如何购买一辆死飞自行车，大概需要花多少钱？',
            },
            '4': {
                'background': '小明准备乘坐飞机去美国留学，他可能需要携带很多行李，所以他想研究一下国际航班对手提行李的重量限制体积限制，对托运行李的重量限制体积限制，手提行李中能携带多少液体，那些物品必须手提，那些物品必须托运等信息。',
                'goal': '请你根据搜索结果，说三点国际航班手提行李的注意事项（重量、禁运物品等）',
            },
            '7': {
                'background': '小明的一个朋友想戒烟，所以他想知道戒烟的好处，戒烟的副作用，有哪些有效的戒烟方式等信息',
                'goal': '请你根据搜索过程中的收获，提三点戒烟的建议（例如：1. 应该保持规律的生活习惯）',
            },
            '8': {
                'background': '小明听说谷歌推出了一款“谷歌眼镜”，他很感兴趣，请查找这种产品的功能、使用方式、售价等信息。',
                'goal': '请你根据搜索过程中的收获，简单说明谷歌眼镜的主要功能',
            },
            '10': {
                'background': '小明想在香港购买一台iphone6，请查找国内和香港的iphone6的售价，如何在香港购买iphone，把iphone带回国内是否需要缴纳关税，港版iphone是否支持国内运营商网络等信息。',
                'goal': '请你根据搜索过程中的收获，说说港版iphone是否对国内移动网络的支持情况等等。',
            },
            '11': {
                'background': '冬天到了，小明想去游泳，请查找清华大学游泳馆的所在地、开放时间、学生票价格、办理游泳卡价格等信息。',
                'goal': '请根据搜索结果，给小明尽可能多地提供一些清华大学游泳馆的基本信息（地址、价格、时间等）',
            },
            '12': {
                'background': '小明最近对军事很感兴趣，所以他想知道中国第一艘航母辽宁号的信息。请帮他查找辽宁号的基本信息（如排水量，舰长，舷宽，船员人数，航速，武器装备等），辽宁号的历史，航母能起到的战略作用，相对于其他国家的航母，辽宁号的优势和劣势等信息。',
                'goal': '请根据搜索结果，给小明尽可能多地提供一些辽宁号的基本信息',
            }
        }

    def load_prompt(self, prompt_path):
        file_names = os.listdir(prompt_path)

        for prompt_name in file_names:
            with open(os.path.join(prompt_path, prompt_name), 'r', encoding='utf-8') as file:
                # 去掉.txt
                self.prompt[prompt_name[:-4]] = file.read()
