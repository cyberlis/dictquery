DictQuery
========================

Library to query python dicts


Suppose we have a dictionary like this:

```
from datetime import datetime
data = {
  "_id": 10,
  "isActive": False,
  "age": 27,
  "eyeColor": "green",
  "name": {
    "firstname": "Marion",
    "secondname": "Delgado",
  },
  "gender": "female",
  "email": "mariondelgado@bleendot.com",
  "registered": datetime.strptime("2015-03-29T06:07:58", "%Y-%m-%dT%H:%M:%S"),
  "latitude": 74.785608,
  "longitude": -112.366088,
  "tags": [
    "voluptate",
    "ex",
    "dolor",
    "aute"
  ],
  "user.address": "155 Village Road, Enetai, Puerto Rico, 2634",
  "friends": [
    {
      "id": 0,
      "name": {
        "firstname": "Ratliff",
        "secondname": "Becker",
      },
      "age": 27,
      "eyeColor": "green"
    },
    {
      "id": 1,
      "name": {
        "firstname": "Raymond",
        "secondname": "Albert",
      },
      "age": 19,
      "eyeColor": "brown"
    },
    {
      "id": 2,
      "name": {
        "firstname": "Mavis",
        "secondname": "Sheppard",
      },
      "age": 34,
      "eyeColor": "blue"
    }
  ]
}
```

Supported data types
====================
| type | example |
|-----------|---------|
| NUMBER    | 42, -12, 34.7 |
| STRING    | 'hello', "hellow" |
| BOOLEAN   | true, false |
| NONE      | none, null |
| NOW       | utc current datetime |
| REGEXP    | /\d+\d+\w+/ |
| ARRAY     | list of any items and any types |


Dict keys
===========
Dict keys literals are written in a variety of ways:
* Single quotes: 'allows embedded "double" quotes'
* Double quotes: "allows embedded 'single' quotes".

DictQuery supports nested dicts splited by dot `.` or any separator specified in `key_separator` param. Default `key_separator='.'`

```
>>> import dictquery as dq
>>> dq.match(data, "'friends.age' <= 26")
True
>>> compiled = dq.compile("'friends/age' <= 26", key_separator='/')
>>> compiled.match(data)
True
```

if you don't need nested keys parsing and want get keys as is or if your keys contain separator char, you can disable nested keys behaviour by setting `use_nested_keys=False`

```
>>> import dictquery as dq
>>> dq.match(data, "'user.address'")
False
>>> compiled = dq.compile("'user.address'", use_nested_keys=False)
>>> compiled.match(data)
True
```

In query you can use dict keys 'as is' without any binary operation. DictQuery will get value by the key and evalute it to bool

```
>>> import dictquery as dq
>>> dq.match(data, "'isActive'")
False
>>> dq.match(data, "'isActive' == false")
True
```

if key is not found by default this situation evalutes to boolean `False` (no exception raised).
You can set `raise_keyerror=True` to raise keyerror if key would not be found.
```
>>> import dictquery as dq
>>> dq.match(data, "'favoriteFruit'")
False
>>> compiled = dq.compile("'favoriteFruit'", raise_keyerror=True)
>>> compiled.match(data)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "dictquery.py", line 355, in match
    return self._eval_expr(query_dict, self.ast)
  File "dictquery.py", line 327, in _eval_expr
    dict_value = self._get_dict_value(query_dict, tree.value)
  File "dictquery.py", line 302, in _get_dict_value
    self.key_separator, self.raise_keyerror)
  File "dictquery.py", line 258, in get_dict_value
    raise DQKeyError("Key '%s' not found" % dict_key)
dictquery.DQKeyError: "Key 'favoriteFruit' not found"

```

Comparisons
===========


| Operation | Meaning |
|-----------|---------|
| <         | strictly less than |
| <=        | less than or equal |
| >         | strictly greater than |
| >=        | greater than or equal |
| ==        | equal |
| !=        | not equal |


```
>>> import dictquery as dq
>>> dq.match(data, "'age' == 26")
True
>>> dq.match(data, "'latitude' > 12")
True
>>> dq.match(data, "'longitude' < 30")
True
>>> dq.match(data, "'friends.age' <= 26")
True
>>> dq.match(data, "'longitude' >= -130")
True
>>> dq.match(data, "'id' != 0")
True
>>> dq.match(data, "'gender' == 'male'")
False
```

String comparisons and matching
===============================

String literals are written in a variety of ways:
* Single quotes: 'allows embedded "double" quotes'
* Double quotes: "allows embedded 'single' quotes".

| Operation | Meaning |
|-----------|---------|
| MATCH     | regexp matching |
| LIKE      | glob like matching |
| IN        | dict item substring in string |
| CONTAIN   | dict item substring contains string |

< , <= , > , >= , == , != works same way with strings as python
```
>>> import dictquery as dq
>>> dq.match(data, "'eyeColor' == 'green'")
True
>>> dq.match(data, "'name.firstname' != 'Ratliff'")
True
>>> dq.match(data, "'eyeColor' IN 'string with green color'")
True
>>> dq.match(data, "'email' CONTAIN '.com'")
True
>>> dq.match(data, r"'email' MATCH /\w+@\w+\.\w+/")
True
>>> dq.match(data, r"'email' LIKE 'mariondelgado@*'")
True
>>> dq.match(data, r"'email' LIKE 'mariondelgado?bleendot?com'")
True
```

By default all string related operations are case sensitive. To change this behaviour you have to create instance of DictQuery with `case_sensitive=False`

```
>>> import dictquery as dq
>>> dq.match(data, "'name.firstname' == 'marion'")
False
>>> compiled = dq.compile("'name.firstname' == 'marion'", case_sensitive=False)
>>> compiled.match(data)
True
```

Array comparisons
=================
| Operation | Meaning |
|-----------|---------|
| IN        | dict item in array |
| CONTAIN   | dict item contains matching item |


```
>>> import dictquery as dq
>>> dq.match(data, "'tags' CONTAIN 'dolor'")
True
>>> dq.match(data, "'eyeColor' IN ['blue', 'green', 'black']")
True
```

Key presence in dict
=====================
`CONTAIN` can be used with dict items to check if key in dict

```
>>> import dictquery as dq
>>> dq.match(data, "'name' CONTAIN 'firstname'")
True
>>> dq.match(data, "'name' CONTAIN 'thirdname'")
False
```

Datetime comparisons with `NOW`
===============================
`NOW` returns current utc datetime

dict item can be compared with `NOW` using standard operations (< , <= , > , >= , == , !=)
```
>>> import dictquery as dq
>>> dq.match(data, "'registered' < NOW")
True
>>> dq.match(data, "'registered' != NOW")
True
```

Logical operators
=================
|Operator|	Meaning|	Example|
|--------|---------|---------|
|and	|True if both the operands are true|	x and y|
|or	|True if either of the operands is true|	x or y|
|not	|True if operand is false (complements the operand)|	not x |

```
>>> import dictquery as dq
>>> dq.match(data, "'isActive' AND 'gender' == 'female'")
False
>>> dq.match(data, "'isActive' OR 'gender' == 'female'")
True
>>> dq.match(data, "NOT 'isActive' AND 'gender' == 'female'")
True
```

You can use parentheses to group statements or change evalution order
```
>>> import dictquery as dq
>>> dq.match(data, "'isActive' AND 'gender' == 'female' OR 'age' == 27")
True
>>> dq.match(data, "'isActive' AND ('gender' == 'female' OR 'age' == 27)")
False
```
