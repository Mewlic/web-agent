import json
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

with open('output/generate_step/direct-none/actions.json', "r", encoding='utf-8') as file:
    json_data = json.load(file)

# query
bleu_score_list_first = []
bleu_score_list_others = []
# click
generate_clicks = []
original_clicks = []
# action
generate_actions = []
original_actions = []

for user_id in json_data:
    for task_id in json_data[user_id]:
        for step in json_data[user_id][task_id]:
            if 'action' in step['type']:
                generate_result = step['content']['generate_result'].strip()
                original_result = step['content']['original_result'].strip()

                if '结束会话' not in generate_result and '结束会话' not in original_result:
                    smoothie = SmoothingFunction().method1
                    bleu_score = sentence_bleu([generate_result], original_result, weights=(0.5, 0.5, 0, 0), smoothing_function=smoothie)

                    if step['step'] == 0:
                        bleu_score_list_first.append(bleu_score)
                    else:
                        bleu_score_list_others.append(bleu_score)

                generate_actions.append(1) if '结束会话' in generate_result else generate_actions.append(0)
                original_actions.append(1) if '结束会话' in original_result else original_actions.append(0)

            if 'clicks' in step['type']:
                generate_result = step['content']['generate_result']
                original_result = step['content']['original_result']

                generate_clicks.extend([1 if x + 1 in generate_result else 0 for x in range(10)])
                original_clicks.extend([1 if x + 1 in original_result else 0 for x in range(10)])

print('--------query--------')

print(sum(bleu_score_list_first) / len(bleu_score_list_first))
print(sum(bleu_score_list_others) / len(bleu_score_list_others))

print('--------click--------')

accuracy = accuracy_score(original_clicks, generate_clicks)
print("Accuracy:", accuracy)
precision = precision_score(original_clicks, generate_clicks)
print("Precision:", precision)
recall = recall_score(original_clicks, generate_clicks)
print("Recall:", recall)
f1 = f1_score(original_clicks, generate_clicks)
print("F1 Score:", f1)

print('--------action--------')

accuracy = accuracy_score(original_actions, generate_actions)
print("Accuracy:", accuracy)
precision = precision_score(original_actions, generate_actions)
print("Precision:", precision)
recall = recall_score(original_actions, generate_actions)
print("Recall:", recall)
f1 = f1_score(original_actions, generate_actions)
print("F1 Score:", f1)
