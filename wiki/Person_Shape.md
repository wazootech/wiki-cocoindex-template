---
id: wiki:PersonShape
type: sh:NodeShape
sh:targetClass: schema:Person
sh:property:
  - sh:path: schema:givenName
    sh:datatype: xsd:string
    sh:minCount: 1
  - sh:path: schema:familyName
    sh:datatype: xsd:string
    sh:minCount: 1
---

# Person shape

Defines validation rules for Person profiles in this wiki.
