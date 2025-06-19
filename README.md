# NTUT-Problem-Repo
The online problem repo for NTUT-Program-Assignment

To add new problem to the database, pelase follow the following format:
```json
{
  "_comment": "",
  "uuid": "Specfiy the uuid or leave it `null` to auto generate",
  "title": "Problem Title",
  "createDate": 0, // Use millisecond since epoch
  "collections": [
    "Specfiy which collection the problem stay (with UUID)","Leave this field `null` to auto generate using folder",
    "UUID-1",
    "UUID-2"
  ],
  "problem": [
    "Problem Line 1",
    "Problem Line 2",
    "...",
    "To add image, please follow the format below",
    "<img src=\"https://image.com/image.png\">"
  ],
  "testcase": {
    "codeType": 1, // 0=Python, 1=C Language
    "cases": [
      {
        "input": [
          "Input Line 1",
          "Input Line 1",
          "..."
        ],
        "output": [
          "Expected Output Line 1",
          "Expected Output Line 2",
          "..."
        ]
      }
    ]
  },
  "sampleCode": [
    "Line 1",
    "Line 2",
    "..."
  ]
}
```

### 程式設計II 112 期末上機考題庫
- ``112_PD2_Final``

### 程式設計II 113 作業
- ``113_PD2_Homework``