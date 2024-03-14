# Как мы генерим конфигурацию

Мы устали собирать конфиг руками, поэтому теперь за нас это будет делать тупая машина

Lur - тул для автосборки структурных правил.

Чтобы собрать правила:
```shell
python3 -m pip lur/requirements.txt
python3 -m lur manifest-to-build.yaml
```
Вместо `manifest-to-build.yaml` подставляете имя цели для сборки из папки `manifests`
Как результат получаете файл: `main.yaml`, который остается загрузить в конфигуратор

## Как писать цели для сборки (/manifests)
Цели первого уровня будут находиться в папке /manifests. Именно эти файлы служат для корневого построения сборки. В сборочных файлах можно использовать две автогенрационные конструкции:

* Макросы - jinja2-макросы, с определенными апгрейдами (смотри подробности в разделе описание правил). Вы можете использовать любой макрос объявленный в специальной директории
```yaml
devices:
  ...
rules:
  - {{ rule_hid_onvif_set_active_camera('cam1', 77) }}
  - {{ rule_hid_onvif_set_active_camera('cam2', 88) }}
```
* Включение групп-правил (смотри /rules_groups) через include
```yaml
devices:
  ...
rules:
  - include: hid-master.yaml
```

## Как писать макросы для правил (/rules)
1) Макросы для правил должны находиться в папке `/rules`
2) Файлы с макросами должны соответстовать маске `*.tpl.yaml` или `*tpl.yml`
3) Имя макроса, который будет использоваться как правило должно начинаться с `rule_`
4) В одном файле может быть любое количество макросов-правил

Пример:
```yaml
{% macro rule_hid_onvif_set_active_camera(camera_alias, key_code) %}
  name: HidSetActive_{{ camera_alias }}_{{ key_code }}
  manipulator_name: hidman
  executor_name: onvifman
  signal_code: KeyReleasedSignal
  command_code: SetCameraActiveCommand
  trigger:
    ==:
      - var: key_code
      - {{ key_code }}
  logic:
    cam_alias: {{ camera_alias }}
{% endmacro %}
```

Если ты больно хитрый и хочешь использовать например параметры по умолчанию, то вы можете сделать это например(см доку макросов в jinja):
```yaml
{% macro rule_hid_onvif_set_active_camera(key_code, camera_alias='cam1') %}
  name: HidSetActive_{{ camera_alias }}_{{ key_code }}
  manipulator_name: hidman
  executor_name: onvifman
  signal_code: KeyReleasedSignal
  command_code: SetCameraActiveCommand
  trigger:
    ==:
      - var: key_code
      - {{ key_code }}
  logic:
    cam_alias: {{ camera_alias }}
{% endmacro %}
```

## Как писать группы правил (/rules_groups)
В целом группы правил не сильно отличаются от манифестов, за исключением того, что они собраны для генерации правил.
1) yaml файлы должны иметь секцию rules
2) В качестве элементов списка можно использовать либо `include: other-file.yaml` (из той же папки), либо макросы правил

## ВАЖНО

>  Вполне возможно в конце вам скажут, что ваш итоговый файл содержит неуникальные имена правил (с указанием того какие имена повторяются), однако файл все равно будет собран. В таком случае стоит посмотреть не генерацию имен