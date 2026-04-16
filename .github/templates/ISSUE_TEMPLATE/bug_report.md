name: 🐛 Bug Report
description: File a bug report to help us improve
body:
  - type: markdown
    attributes:
      value: "Please provide as much detail as possible!"
  - type: input
    id: version
    attributes:
      label: Version
      placeholder: e.g., v1.0.4
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      placeholder: "1. ...\n2. ..."
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
