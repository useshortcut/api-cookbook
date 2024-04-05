name: 🐞 Bug Report
description: File a new bug report
title: '[Bug]: <title>'
labels: [bug, needs-triage]
body:
  - type: markdown
    attributes:
      value: ':stop_sign: _For Shortcut support questions, please visit our [help center](https://help.shortcut.com) instead._'
  - type: checkboxes
    attributes:
      label: 'Do I have the most recent api-cookbook code?'
      description: 'Please ensure you have pulled the latest code from the main branch of https://github.com/useshortcut/app-cookbook'
      options:
      - label: 'I am using the most recent available api-cookbook code.'
        required: true
  - type: checkboxes
    attributes:
      label: 'Is there an existing issue for this?'
      description: 'Please [search :mag: the issues](https://github.com/useshortcut/app-cookbook/issues) to check if this bug has already been reported.'
      options:
      - label: 'I have searched the existing issues'
        required: true
  - type: textarea
    attributes:
      label: 'Current Behavior'
      description: 'Describe the problem you are experiencing, including any console output or screenshots.'
    validations:
      required: true
  - type: textarea
    attributes:
      label: 'Expected Behavior'
      description: 'Describe what you expect to happen instead.'
    validations:
      required: true
  - type: textarea
    attributes:
      label: 'Minimal Reproducible Example'
      description: |
        Please provide a the _smallest, complete example_ that the api-cookbook's maintainers can run to reproduce the issue ([read more about what this entails](https://stackoverflow.com/help/minimal-reproducible-example)).  Failing this, any sort of reproduction steps are better than nothing!

        If you have sensitive data, remember that this is a public repository and you should anonymize or blur any information you don't want to be shared publicly.

        If the result is more than a screenful of text _or_ requires multiple files, please:

        - _Attach_ (do not paste) it to this textarea, _or_
        - Put it in a [Gist](https://gist.github.com) and paste the link, _or_
        - Provide a link to a new or existing public repository exhibiting the issue.
    validations:
      required: true
  - type: textarea
    attributes:
      label: 'Environment'
      description: 'Please provide the following information about your environment; feel free to remove any items which are not relevant. If you need to share sensitive information or have a question specific to your Shortcut workspace, please submit a [help center request](https://help.shortcut.com/hc/en-us/requests/new) instead.'
      value: |
          - Operating system:
          - Python/JavaScript version:
    validations:
      required: false
  - type: textarea
    attributes:
      label: Further Information
      description: |
        Links? References? Anything that will give us more context about the issue you are encountering!

        _Tip: You can attach images or log files by clicking this area to highlight it and then dragging files in._
    validations:
      required: false
  - type: markdown
    attributes:
      value: ':stop_sign: _For Shortcut support questions, please visit our [help center](https://help.shortcut.com) instead._'

