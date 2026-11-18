# E1 / test 真实运行样例

## 一、正确样例（2 个）

### 1. 样本 `test_0000`（doc: `24_7ecbplus.xml.xml`）

- **原文**：The police source , who wished to remain anonymous , said the men drove a large 4×4 car into the store in the early hours of the morning , and grabbed jewellery and luxury watches worth an estimated €2 million .
- **源事件**：estimated　**目标事件**：said
- **真实标签**：无因果　**预测标签**：无因果
- **决策路径**：filtered（q=0，Z=None）

### 2. 样本 `test_0001`（doc: `20_3ecbplus.xml.xml`）

- **原文**：An earthquake measuring at least magnitude - 5 . 9 shook a sparsely populated area of southern Iran on Sunday , flattening seven villages and killing 10 people , officials said .
- **源事件**：said　**目标事件**：earthquake
- **真实标签**：无因果　**预测标签**：无因果
- **决策路径**：filtered（q=0，Z=None）


## 二、错例（5 个）

### 1. 样本 `test_0002`（doc: `35_2ecbplus.xml.xml`）

- **原文**：Another Charger , receiver Vincent Jackson , was arrested early Jan . 6 on suspicion of driving under the influence on state Route 52 near Interstate 805 .
- **源事件**：on suspicion　**目标事件**：arrested
- **真实标签**：无因果　**预测标签**：有因果
- **决策路径**：reasoner（q=3，Z=None）

### 2. 样本 `test_0003`（doc: `18_3ecbplus.xml.xml`）

- **原文**："A man suspected of shooting three people , killing one , at an accounting firm where was fired last week was arrested after a high - speed chase a few hours after the Monday morning attack , authorities said .
- **源事件**：killing　**目标事件**：chase
- **真实标签**：无因果　**预测标签**：有因果
- **决策路径**：reasoner（q=3，Z=None）

### 3. 样本 `test_0009`（doc: `23_11ecbplus.xml.xml`）

- **原文**：Mr Buckley's death came a day after 36 - year - old Duncan Raite died when he slipped and fell around 200ft from a ridge in the same national park .
- **源事件**：slipped　**目标事件**：died
- **真实标签**：无因果　**预测标签**：有因果
- **决策路径**：reasoner（q=3，Z=None）

### 4. 样本 `test_0020`（doc: `3_3ecbplus.xml.xml`）

- **原文**：His supervision was revoked and he returned to prison in May 1984 with a new charge of indecency with a child , given a new 20 year sentence .
- **源事件**：sentence　**目标事件**：indecency
- **真实标签**：有因果　**预测标签**：无因果
- **决策路径**：filtered（q=0，Z=None）

### 5. 样本 `test_0025`（doc: `8_2ecbplus.xml.xml`）

- **原文**：A fire - bomb attack on a bank in Greece killed at least three people Wednesday as police fought pitched battles with striking protestors furious at brutal budget cuts designed to avert national bankruptcy .
- **源事件**：battles　**目标事件**：fought
- **真实标签**：有因果　**预测标签**：无因果
- **决策路径**：filtered（q=0，Z=None）
