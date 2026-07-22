---
id: wiki:ProjectShape
type: sh:NodeShape
sh:targetClass: schema:SoftwareApplication
sh:property:
  - sh:path: schema:name
    sh:datatype: xsd:string
    sh:minCount: 1
  - sh:path: schema:description
    sh:datatype: xsd:string
    sh:minCount: 1
---

# Project shape

Defines validation rules for the template project metadata used in examples and tests.
