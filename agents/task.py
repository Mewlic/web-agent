from agents.recagent import RecAgent
from agents.crawler import Crawler


class Task:
    def __init__(self, task_id: str, prompt: dict, background: dict, agent: RecAgent, strategy: str, mode: str,
                 actions: list, task: list = None):
        if mode == 'generate_step':
            self.task = task
            if 'reasoning' in strategy:
                self.task.append(dict())    # 加一个新的dict，用于存放最后一次生成的thought
        elif mode == 'generate_session':
            self.task = []
        self.task_id = task_id
        self.prompt = prompt
        self.background = background
        self.agent = agent
        self.strategy = strategy
        self.mode = mode
        self.actions = actions

    def get_history(self, end_step: int) -> str:
        """
        生成会话的历史操作，格式：
        [思考1：thought_1]
        行动1：搜索[query_1]
        观察1：observation_1
        [思考2：thought_2]
        ...
        思考n：thought_n
        行动n:结束会话
        """
        suffix = ''
        step = 0

        for qu_pair in self.task:
            if 'thought' in qu_pair:
                thought = qu_pair['thought'].strip()
                suffix += '思考' + str(step // 2 + 1) + '：' + thought + '\n'

            if step == end_step:
                break
            step += 1

            if 'query' in qu_pair:
                query = qu_pair['query'].strip()
                suffix += '行动' + str(step // 2 + 1) + '：搜索[' + query + ']\n'

            if step == end_step:
                break
            step += 1

            if 'observation' in qu_pair:
                observation = qu_pair['observation'].strip()
                suffix += '观察' + str(step // 2) + '：' + observation + '\n'

        if suffix != '':
            suffix = '\n以下是你已经执行了的操作：\n' + suffix

        return suffix

    def get_suffix_A(self, step: int) -> str:
        """
        得到prompt_suffix的A段
        A段主要给出例子（example）或总结（summary）来指导agent工作
        """
        if self.strategy in ['direct-example']:
            suffix = self.prompt['direct-example_A']
        elif self.strategy in ['direct-summary']:
            suffix = self.prompt['direct-summary_A']
        elif self.strategy in ['reasoning-example']:
            suffix = self.prompt['reasoning-example_A']
        elif self.strategy in ['reasoning-summary']:
            suffix = self.prompt['reasoning-summary_A']
        elif self.strategy in ['multi_level-example']:
            suffix = self.prompt['direct-example_A'] if step % 2 == 0 else self.prompt['multi_level-example_Al']
        elif self.strategy in ['multi_level-summary']:
            suffix = self.prompt['direct-summary_A'] if step % 2 == 0 else self.prompt['multi_level-summary_A']
        elif self.strategy in ['reasoning-multi_level-example']:
            suffix = self.prompt['reasoning-example_A'] if step % 2 == 0 else self.prompt['multi_level-example_A']
        elif self.strategy in ['reasoning-multi_level-summary']:
            suffix = self.prompt['reasoning-summary_A'] if step % 2 == 0 else self.prompt['multi_level-summary_A']
        else:
            suffix = ''
        return suffix

    def get_suffix_B(self, step: int) -> str:
        """
        得到prompt_suffix的B段
        B段主要给出当前会话的历史操作(包含生成thought)
        """
        if step % 2 == 0 and 'reasoning' in self.strategy:  # 生成thought
            suffix_A = self.get_suffix_A(step)
            suffix_B = self.get_history(step)

            prompt_str = self.prompt['background'] + suffix_A + suffix_B + self.prompt['action_reasoning_thought_C']
            prompt_dict = dict(
                background=self.background[self.task_id]["background"],
                goal=self.background[self.task_id]["goal"],
                step=str(step // 2 + 1),
            )
            generate_thought = self.agent.generate(prompt_str, prompt_dict)
            clean_thought = generate_thought[generate_thought.find("：") + 1:].strip()

            self.task[step // 2]['thought'] = clean_thought

            if self.mode == 'generate_session':
                self.actions.append({
                    'type': 'thought',
                    'content': clean_thought,
                    'step': step // 2
                })

        suffix = self.get_history(step)

        if step % 2 == 0 and 'reasoning' in self.strategy and self.mode == 'generate_step':
            del self.task[step // 2]['thought']

        return suffix

    def get_suffix_C(self, step: int, substring_len: int) -> str:
        """
        得到prompt_suffix的C段
        C段用来给出要求，指导anent输出正确的格式
        """
        if step % 2 == 0:
            if 'reasoning' not in self.strategy:
                suffix = self.prompt['action_direct_C']
            else:
                suffix = self.prompt['action_reasoning_action_C']

        elif step % 2 == 1:
            if self.mode == 'generate_session':
                query = self.task[step // 2]['query']

                crawler = Crawler()
                results = crawler.SearchResultCrawl(query)

                self.task[step // 2]['results'] = results

                self.actions.append({
                    'type': 'results',
                    'content': results,
                    'step': step // 2
                })

            prompt_results = '\n'
            num = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
            for rank, result in enumerate(self.task[step // 2]['results'][:10]):
                prompt_results += '第' + num[rank] + '条：' + result['content'].strip().replace("{", "").replace("}", "")[
                                                           :substring_len] + '；\n'
            suffix = '搜索结果如下：' + prompt_results + self.prompt['click_C']
        else:
            suffix = ''

        return suffix

    def predict_thought(self, step: int) -> None:
        """
        已知background、query和click的情况下预测thought
        用于在reasoning策略中补全数据集
        """
        suffix_A = self.get_suffix_A(step)
        suffix_B = self.get_history(step)

        prompt_str = self.prompt['background'] + suffix_A + suffix_B + self.prompt['action_reasoning_predict_thought_C']
        prompt_dict = dict(
            background=self.background[self.task_id]["background"],
            goal=self.background[self.task_id]["goal"],
            step=str(step // 2 + 1),
        )
        generate_thought = self.agent.generate(prompt_str, prompt_dict)
        clean_thought = generate_thought[generate_thought.find("：") + 1:].strip()
        self.task[step // 2]['thought'] = clean_thought

    def generate_observation(self, step: int, substring_len: int) -> None:
        """
        用于生成observation
        """
        success = 1     # 爬虫成功爬取网页正文内容
        suffix_A = self.get_suffix_A(step)
        suffix_B = self.get_history(step)

        click_list = [int(num) for num in self.task[step // 2]['clicks'].split(',')]

        crawler = Crawler()
        observation = ''
        for rank, result in enumerate(self.task[step // 2]['results']):
            if rank in click_list:
                # 第一次观察
                content = crawler.UrlCrawl(result['url'])
                if content is None or content == '':
                    content = result['content']
                    success = 0

                suffix_obv = '对于最后一次搜索行动，点击结果页面如下：\n' + content.strip().replace("{", "").replace("}", "")[:substring_len] + '\n'

                prompt_str = self.prompt['background'] + suffix_A + suffix_B + suffix_obv + self.prompt['action_reasoning_observation_C']
                prompt_dict = dict(
                    background=self.background[self.task_id]["background"],
                    goal=self.background[self.task_id]["goal"],
                    step=str(step // 2 + 1),
                )
                generate_observation = self.agent.generate(prompt_str, prompt_dict)

                # 第二次观察，爬取网页失败，使用SERP的内容
                if success == 1 and '观察失败' in generate_observation:
                    success = 0
                    content = result['content']

                    suffix_obv = '对于最后一次搜索行动，点击结果页面如下：\n' + content.strip().replace("{", "").replace("}", "")[
                                                            :substring_len] + '\n'

                    prompt_str = self.prompt['background'] + suffix_A + suffix_B + suffix_obv + self.prompt[
                        'action_reasoning_observation_C']
                    prompt_dict = dict(
                        background=self.background[self.task_id]["background"],
                        goal=self.background[self.task_id]["goal"],
                        step=str(step // 2 + 1),
                    )
                    generate_observation = self.agent.generate(prompt_str, prompt_dict)

                clean_observation = generate_observation[generate_observation.find("：") + 1:].strip()
                if '观察失败' not in generate_observation:
                    observation += clean_observation + '\n'

                result['success'] = success

        if observation == '':
            observation = '观察失败'

        self.task[step // 2]['observation'] = observation

        if self.mode == 'generate_session':
            self.actions.append({
                'type': 'observation',
                'content': observation,
                'step': step // 2
            })

    def generate_step(self, step: int, max_result_token: int, max_content_token: int) -> tuple:
        end = 0
        if step % 2 == 1 and 'reasoning' in self.strategy:
            self.predict_thought(step)                      # 预测thought

        suffix_A = self.get_suffix_A(step)                    # 指导
        suffix_B = self.get_suffix_B(step)                    # 历史
        suffix_C = self.get_suffix_C(step, max_result_token)  # 要求

        # 生成行动
        prompt_str = self.prompt['background'] + suffix_A + suffix_B + suffix_C
        prompt_dict = dict(
            background=self.background[self.task_id]["background"],
            goal=self.background[self.task_id]["goal"],
            step=str(step // 2 + 1),
        )
        generate_result = self.agent.generate(prompt_str, prompt_dict)

        if step % 2 == 0:
            if step // 2 < len(self.task) and 'query' in self.task[step // 2]:
                original_result = self.task[step // 2]['query']
            else:
                original_result = '结束会话'
                end = 1

            if '结束会话' in generate_result:
                generate_result = '结束会话'
            else:
                start_index = generate_result.find("[") + 1
                end_index = generate_result.find("]")
                generate_result = generate_result[start_index:end_index].strip()

            self.actions.append({
                'type': 'action',
                'content': {
                    'generate_result': generate_result,
                    'original_result': original_result,
                },
                'step': step // 2
            })

        elif step % 2 == 1:
            self.generate_observation(step, max_content_token)

            original_result_str = self.task[step // 2]['clicks']
            original_result = [int(num) for num in original_result_str.split(',')]

            start_index = generate_result.find("：") + 1
            if start_index == 0:
                start_index = generate_result.find(":") + 1
            generate_result = generate_result[start_index:].strip()
            generate_result = [int(num) - 1 for num in generate_result.split(",") if num.strip() != ""]

            self.actions.append({
                'type': 'clicks',
                'content': {
                    'generate_result': generate_result,
                    'original_result': original_result
                },
                'step': step // 2
            })

        return self.actions, end

    def generate_session(self, step: int, max_result_token: int, max_content_token: int) -> tuple:
        end = 0
        if len(self.task) < step // 2 + 1:
            self.task.append(dict())

        suffix_A = self.get_suffix_A(step)
        suffix_B = self.get_suffix_B(step)
        suffix_C = self.get_suffix_C(step, max_result_token)

        # 生成行动
        prompt_str = self.prompt['background'] + suffix_A + suffix_B + suffix_C
        prompt_dict = dict(
            background=self.background[self.task_id]["background"],
            goal=self.background[self.task_id]["goal"],
            step=str(step // 2 + 1),
        )
        generate_result = self.agent.generate(prompt_str, prompt_dict)

        if step % 2 == 0:
            if '结束会话' in generate_result:
                generate_result = '结束会话'
                end = 1
            else:
                start_index = generate_result.find("[") + 1
                end_index = generate_result.find("]")
                generate_result = generate_result[start_index:end_index].strip()

            self.task[step // 2]['query'] = generate_result

            self.actions.append({
                'type': 'action',
                'content': generate_result,
                'step': step // 2
            })

        elif step % 2 == 1:
            start_index = generate_result.find("：") + 1
            if start_index == 0:
                start_index = generate_result.find(":") + 1
            generate_result = [int(num) - 1 for num in generate_result[start_index:].strip().split(",") if num.strip() != ""]
            self.task[step // 2]['clicks'] = ','.join(str(num) for num in generate_result)

            self.actions.append({
                'type': 'clicks',
                'content': generate_result,
                'step': step // 2
            })

            self.generate_observation(step, max_content_token)

        return self.actions, end
