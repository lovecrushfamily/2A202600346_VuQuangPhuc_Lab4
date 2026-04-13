# TravelBuddy - LangGraph Travel Agent

## 1. Giới thiệu

Đây là bài Lab 4 xây dựng một AI Agent tên **TravelBuddy** bằng **LangGraph**.
Agent có nhiệm vụ hỗ trợ người dùng trong các tình huống du lịch như:

- tìm chuyến bay
- tìm khách sạn
- tính toán ngân sách chuyến đi
- từ chối các câu hỏi không liên quan đến du lịch

Project sử dụng:

- `LangGraph` để điều phối luồng agent
- `LangChain` để bind tool
- `OpenRouter` với model `qwen/qwen3.6-plus:free`
- `python-dotenv` để đọc API key từ file `.env`

---

## 2. Cấu trúc file

- `agent.py`: file chính, khởi tạo LLM, bind tools, build LangGraph và chạy vòng lặp chat
- `tools.py`: chứa mock data và 3 custom tools
- `system_prompt.txt`: định nghĩa persona, rules, tool instruction, response format và constraints
- `test_api.py`: file test kết nối API riêng
- `test_results.md`: log kết quả 5 test case
- `.env`: chứa `OPENROUTER_API_KEY`

---

## 3. Cách chạy project

### 3.1. Di chuyển vào thư mục project

```bash
cd /home/lovecrush/Documents/2A202600346_Lab4
```

### 3.2. Kích hoạt virtual environment

Mac/Linux:

```bash
source venv/bin/activate
```

Hoặc có thể chạy trực tiếp bằng Python trong `venv` mà không cần activate:

```bash
./venv/bin/python test_api.py
./venv/bin/python agent.py
```

### 3.3. Kiểm tra API trước

```bash
python test_api.py
```

Nếu API hoạt động bình thường, chương trình sẽ in ra một câu chào từ model.

### 3.4. Chạy agent chính

```bash
python agent.py
```

Thoát chương trình bằng:

```text
quit
```

hoặc:

```text
exit
```

hoặc:

```text
q
```

### 3.5. Lưu ý khi chạy

- Cần có file `.env` với biến `OPENROUTER_API_KEY`
- Nên chạy bằng Python trong thư mục `venv`, nếu dùng `python3` hệ thống có thể bị lỗi thiếu package như `langgraph` hoặc `langchain_openrouter`
- Vì đang dùng model free của OpenRouter nên đôi lúc có thể gặp lỗi upstream tạm thời

---

## 4. Mô tả 3 tools trong `tools.py`

### 4.1. `search_flights(origin, destination)`

Chức năng:

- tra cứu chuyến bay giữa 2 thành phố
- đọc dữ liệu từ `FLIGHTS_DB`
- nếu không có chuyến trực tiếp thì thử kiểm tra chiều ngược lại
- trả về danh sách chuyến bay gồm hãng, giờ bay, hạng vé và giá

### 4.2. `search_hotels(city, max_price_per_night=9999999)`

Chức năng:

- tra cứu khách sạn theo thành phố
- lọc theo mức giá tối đa mỗi đêm
- sắp xếp khách sạn theo `rating` giảm dần
- trả về danh sách khách sạn phù hợp

### 4.3. `calculate_budget(total_budget, expenses)`

Chức năng:

- nhận tổng ngân sách ban đầu
- nhận chuỗi chi phí dạng `ten_khoan:so_tien`
- cộng toàn bộ chi phí
- tính phần còn lại của ngân sách
- nếu vượt ngân sách thì thông báo số tiền bị thiếu

Ví dụ input:

```text
vé_máy_bay:2200000,khách_sạn:400000,ăn_uống:1500000
```

---

## 5. Luồng chạy của LangGraph

Project này dùng một graph rất gọn gồm 2 node chính:

- `agent`
- `tools`

### 5.1. Sơ đồ ASCII

```text
                 +------------------+
                 |      START       |
                 +---------+--------+
                           |
                           v
                 +------------------+
                 |      agent       |
                 |  - đọc messages  |
                 |  - thêm prompt   |
                 |  - gọi LLM       |
                 +----+--------+----+
                      |        |
          không cần tool       | cần tool
                      |        v
                      |  +------------------+
                      |  |      tools       |
                      |  | chạy tool tương  |
                      |  | ứng do LLM chọn  |
                      |  +--------+---------+
                      |           |
                      +-----------+
                                  |
                                  v
                        quay lại node `agent`
                                  |
                                  v
                               END
```

### 5.2. Giải thích từng bước

1. Người dùng nhập câu hỏi trong CLI.
2. `graph.invoke(...)` được gọi với message của user.
3. Node `agent` nhận state hiện tại.
4. Nếu message đầu tiên chưa phải `SystemMessage`, chương trình tự chèn `SYSTEM_PROMPT`.
5. `llm_with_tools.invoke(messages)` được gọi.
6. Nếu model trả lời trực tiếp, graph kết thúc.
7. Nếu model yêu cầu tool, `tools_condition` sẽ điều hướng sang node `tools`.
8. `ToolNode` chạy đúng tool mà model yêu cầu.
9. Kết quả tool được đưa lại vào state message.
10. Graph quay về node `agent`.
11. Agent đọc tiếp toàn bộ context mới rồi sinh ra câu trả lời cuối cùng cho user.

---

## 6. Cách `bind_tools()` hoạt động trong project này

Trong `agent.py`, đoạn code quan trọng là:

```python
tools_list = [search_flights, search_hotels, calculate_budget]
llm_with_tools = llm.bind_tools(tools_list)
```

Ý nghĩa:

- `search_flights`, `search_hotels`, `calculate_budget` đều được đánh dấu bằng decorator `@tool`
- decorator này biến các hàm Python thành tool có metadata rõ ràng
- metadata đó gồm tên tool, mô tả, danh sách tham số, kiểu dữ liệu đầu vào
- khi gọi `llm.bind_tools(tools_list)`, LangChain gửi mô tả các tool này cho model

Kết quả là model sẽ biết:

- đang có những tool nào
- tên chính xác của từng tool
- khi nào nên gọi tool nào
- arguments của mỗi tool phải có dạng gì

Ví dụ:

- nếu user hỏi: `Tìm giúp tôi chuyến bay từ Hà Nội đến Đà Nẵng`
- model có thể sinh ra một `tool_call` với:

```text
name = search_flights
args = {"origin": "Hà Nội", "destination": "Đà Nẵng"}
```

Sau đó:

- `tools_condition` phát hiện có `tool_calls`
- graph chuyển sang node `tools`
- `ToolNode(tools_list)` tự tìm đúng tool theo tên
- tool được chạy với arguments tương ứng
- output của tool lại được đưa ngược về cho agent

Điểm quan trọng là:

- model **không tự chạy Python function**
- model chỉ **ra quyết định sẽ gọi tool nào**
- `ToolNode` mới là phần **thực thi tool thật**

---

## 7. Giải thích `system_prompt.txt`

File `system_prompt.txt` được viết theo kiểu XML-like để tách rõ từng vai trò.

### 7.1. `<persona>`

Phần này định nghĩa nhân vật của agent:

- là trợ lý du lịch của TravelBuddy
- thân thiện
- hiểu du lịch Việt Nam
- nói chuyện tự nhiên, không robot

Mục tiêu của phần này là làm cho câu trả lời có màu sắc nhất quán.

### 7.2. `<rules>`

Phần này định nghĩa quy tắc bắt buộc:

- trả lời bằng tiếng Việt
- xưng hô kiểu `cậu - tớ`
- dùng phong cách vui vẻ

Nhờ đó, toàn bộ câu trả lời giữ cùng một giọng điệu.

### 7.3. `<tools_instruction>`

Phần này cho model biết:

- hệ thống có 3 tool
- nên dùng `search_flights` khi hỏi chuyến bay
- nên dùng `search_hotels` khi hỏi khách sạn
- nên dùng `calculate_budget` khi có ngân sách và các khoản chi
- nếu thiếu thông tin quan trọng thì phải hỏi lại trước

Đây là phần rất quan trọng vì nó định hướng cho model biết **khi nào dùng tool**, thay vì trả lời đoán mò.

### 7.4. `<response_format>`

Phần này ép model trình bày câu trả lời theo 4 mục:

- Chuyến bay
- Khách sạn
- Tổng chi phí ước tính
- Gợi ý thêm

Lợi ích:

- câu trả lời đồng đều
- dễ đọc
- phù hợp với các bài test travel-planning

### 7.5. `<constraints>`

Phần này đặt guardrail:

- từ chối các câu hỏi không liên quan tới du lịch
- tránh bị kéo sang bài tập code, chính trị, tài chính, nấu ăn...

Ví dụ:

- câu hỏi về Linked List phải bị từ chối
- câu hỏi về đặt vé hay khách sạn thì được hỗ trợ

---

## 8. Test cases trong `test_results.md`

File `test_results.md` đã lưu lại 5 test case chính của agent.

### Test 1 - Direct Answer

Input:

```text
Xin chào !, Tôi đang muốn đi du lịch nhưng chưa biết đi đâu
```

Mục tiêu:

- agent không cần gọi tool
- agent hỏi thêm về sở thích, thời gian, ngân sách

Kết quả:

- pass
- log cho thấy `LLMs Answer Directly`

### Test 2 - Single Tool Call

Input:

```text
Tìm giúp tôi chuyến bay từ Hà Nội đến Đà Nẵng
```

Mục tiêu:

- agent gọi `search_flights("Hà Nội", "Đà Nẵng")`
- trả về danh sách chuyến bay

Kết quả:

- pass
- log có `Call Tools: search_flights`

### Test 3 - Multi-step Tool Chaining

Input:

```text
Tôi ở Hà Nội muốn đi Phú Quốc 2 đêm budget 5 triệu , tư vấn giúp
```

Mục tiêu:

- gọi `search_flights`
- gọi `search_hotels`
- gọi `calculate_budget`
- tổng hợp thành một câu trả lời cuối

Kết quả:

- pass
- log có đủ 3 tool:
  - `search_flights`
  - `search_hotels`
  - `calculate_budget`

### Test 4 - Missing Information

Input:

```text
Tôi muốn đặt khách sạn!
```

Mục tiêu:

- agent chưa đủ dữ kiện để gọi tool
- phải hỏi lại thành phố, số đêm, ngân sách

Kết quả:

- pass
- agent hỏi lại thông tin cần thiết trước khi hành động

### Test 5 - Guardrail / Refusal

Input:

```text
Giải pháp giúp tôi giải bàoi tập Python về Linked List
```

Mục tiêu:

- agent phải từ chối lịch sự
- nhắc lại phạm vi hỗ trợ chỉ là du lịch

Kết quả:

- pass
- agent từ chối đúng định hướng của prompt

---

## 9. Cách chương trình chạy trong `agent.py`

Tóm tắt nhanh luồng runtime:

```text
user_input
   |
   v
graph.invoke({"messages": [("human", user_input)]})
   |
   v
agent_node(...)
   |
   +--> thêm SystemMessage nếu cần
   |
   +--> llm_with_tools.invoke(messages)
           |
           +--> nếu có tool_calls -> sang ToolNode
           |
           +--> nếu không có tool_calls -> trả lời luôn
   |
   v
ToolNode chạy tool
   |
   v
quay lại agent_node
   |
   v
in kết quả cuối cùng ra CLI
```

---

## 10. Kết luận

TravelBuddy trong project này đã đáp ứng các yêu cầu chính của bài lab:

- có system prompt rõ ràng
- có 3 custom tools với mock data
- build đúng graph bằng LangGraph
- chạy được cả trường hợp direct answer, single tool, multi-step tool chaining và refusal

Đây là một ví dụ đơn giản nhưng khá đầy đủ để hiểu cách xây dựng AI Agent bằng LangGraph theo hướng:

- model ra quyết định
- tool thực thi dữ liệu
- graph điều phối luồng hội thoại
