import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/device.dart';
import '../theme/app_theme.dart';

class DeviceDialog extends StatefulWidget {
  final Device? device;
  final bool Function(String ip, {String? excludeId}) ipExists;
  const DeviceDialog({super.key, this.device, required this.ipExists});

  @override
  State<DeviceDialog> createState() => _DeviceDialogState();
}

class _DeviceDialogState extends State<DeviceDialog> {
  final _formKey   = GlobalKey<FormState>();
  late final TextEditingController _nameCtrl;
  late final TextEditingController _ipCtrl;
  late final TextEditingController _portCtrl;
  late final TextEditingController _glowColorCtrl;
  late final TextEditingController _glowWidthCtrl;

  late DeviceType _deviceType;
  late PingMode   _pingMode;

  // Доступні кольори свічення
  static const _glowPresets = [
    {'label': '🟢 Зелений',  'hex': '#3fb950'},
    {'label': '🔵 Синій',    'hex': '#388bfd'},
    {'label': '🟣 Фіолетовий','hex': '#bc8cff'},
    {'label': '🟡 Жовтий',  'hex': '#d29922'},
    {'label': '🔴 Червоний', 'hex': '#f85149'},
    {'label': '⚪ Білий',    'hex': '#e6edf3'},
  ];

  @override
  void initState() {
    super.initState();
    final d = widget.device;
    _nameCtrl      = TextEditingController(text: d?.name ?? '');
    _ipCtrl        = TextEditingController(text: d?.ip   ?? '10.60.93.');
    _portCtrl      = TextEditingController(text: d?.port.toString() ?? '8080');
    _glowColorCtrl = TextEditingController(text: d?.glowColorHex ?? '#3fb950');
    _glowWidthCtrl = TextEditingController(text: (d?.glowWidth ?? 12.0).toString());
    _deviceType    = d?.deviceType ?? DeviceType.raspberry;
    _pingMode      = d?.pingMode   ?? PingMode.tcp;
  }

  @override
  void dispose() {
    _nameCtrl.dispose(); _ipCtrl.dispose(); _portCtrl.dispose();
    _glowColorCtrl.dispose(); _glowWidthCtrl.dispose();
    super.dispose();
  }

  void _onTypeChanged(DeviceType? t) {
    if (t == null) return;
    setState(() {
      _deviceType = t;
      final cur = int.tryParse(_portCtrl.text) ?? 0;
      if ([8080, 80].contains(cur)) _portCtrl.text = t.defaultPort.toString();
    });
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final glowW = double.tryParse(_glowWidthCtrl.text) ?? 12.0;
    Navigator.of(context).pop(Device(
      id:           widget.device?.id ?? 'dev_${DateTime.now().millisecondsSinceEpoch}',
      name:         _nameCtrl.text.trim(),
      ip:           _ipCtrl.text.trim(),
      port:         int.parse(_portCtrl.text.trim()),
      deviceType:   _deviceType,
      pingMode:     _pingMode,
      glowColorHex: _glowColorCtrl.text.trim(),
      glowWidth:    glowW.clamp(4.0, 40.0),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.device != null;
    return AlertDialog(
      title: Text(isEdit ? 'Редагувати пристрій' : 'Додати пристрій'),
      content: SizedBox(
        width: double.maxFinite,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _field('Назва', _nameCtrl, hint: 'NRK-1',
                  validator: (v) => v?.trim().isEmpty == true ? 'Введіть назву' : null),
                const SizedBox(height: 10),
                _field('IP-адреса', _ipCtrl, hint: '10.60.93.50',
                  keyboard: TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Введіть IP';
                    final p = v.trim().split('.');
                    if (p.length != 4 || p.any((x) => int.tryParse(x) == null))
                      return 'Невірний формат IP';
                    if (widget.ipExists(v.trim(), excludeId: widget.device?.id))
                      return 'IP вже існує';
                    return null;
                  }),
                const SizedBox(height: 10),
                _field('Порт', _portCtrl, hint: '8080',
                  keyboard: TextInputType.number,
                  formatters: [FilteringTextInputFormatter.digitsOnly],
                  validator: (v) {
                    final p = int.tryParse(v ?? '');
                    return (p == null || p < 1 || p > 65535) ? 'Порт 1–65535' : null;
                  }),
                const SizedBox(height: 10),
                _label('Тип пристрою'),
                const SizedBox(height: 4),
                _dropdown<DeviceType>(
                  value: _deviceType,
                  items: DeviceType.values,
                  label: (t) => t.label,
                  onChanged: _onTypeChanged,
                ),
                const SizedBox(height: 10),
                _label('Режим перевірки'),
                const SizedBox(height: 4),
                _dropdown<PingMode>(
                  value: _pingMode,
                  items: PingMode.values,
                  label: (m) => m.label,
                  onChanged: (v) => v != null ? setState(() => _pingMode = v) : null,
                ),

                // ── Свічення ──────────────────────────────────────
                const SizedBox(height: 14),
                const Divider(color: AppTheme.border),
                _label('🌟 Свічення онлайн'),
                const SizedBox(height: 8),

                // Колір — пресети
                Wrap(
                  spacing: 6, runSpacing: 6,
                  children: _glowPresets.map((p) {
                    final hex      = p['hex']!;
                    final selected = _glowColorCtrl.text == hex;
                    Color c;
                    try { c = Color(int.parse(hex.replaceFirst('#', '0xFF'))); }
                    catch (_) { c = AppTheme.online; }
                    return GestureDetector(
                      onTap: () => setState(() => _glowColorCtrl.text = hex),
                      child: Container(
                        width: 32, height: 32,
                        decoration: BoxDecoration(
                          color:  c,
                          shape:  BoxShape.circle,
                          border: Border.all(
                            color: selected ? AppTheme.textMain : Colors.transparent,
                            width: 2.5,
                          ),
                          boxShadow: selected
                              ? [BoxShadow(color: c.withOpacity(0.6), blurRadius: 8)]
                              : null,
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 8),
                _field('Hex колір', _glowColorCtrl, hint: '#3fb950'),
                const SizedBox(height: 10),

                // Ширина свічення
                _label('Ширина свічення: ${_glowWidthCtrl.text}px'),
                Slider(
                  value:    double.tryParse(_glowWidthCtrl.text)?.clamp(4.0, 40.0) ?? 12.0,
                  min:      4.0,
                  max:      40.0,
                  divisions: 18,
                  activeColor:   AppTheme.accent,
                  inactiveColor: AppTheme.border,
                  onChanged: (v) => setState(() => _glowWidthCtrl.text = v.round().toString()),
                ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Скасувати')),
        ElevatedButton(onPressed: _submit, child: Text(isEdit ? 'Зберегти' : 'Додати')),
      ],
    );
  }

  Widget _label(String t) => Text(t,
    style: const TextStyle(color: AppTheme.textDim, fontSize: 11));

  Widget _field(String label, TextEditingController ctrl, {
    String? hint,
    TextInputType? keyboard,
    List<TextInputFormatter>? formatters,
    FormFieldValidator<String>? validator,
  }) => TextFormField(
    controller: ctrl,
    keyboardType: keyboard,
    inputFormatters: formatters,
    validator: validator,
    style: const TextStyle(color: AppTheme.textMain, fontSize: 13),
    decoration: InputDecoration(labelText: label, hintText: hint),
  );

  Widget _dropdown<T>({
    required T value,
    required List<T> items,
    required String Function(T) label,
    required void Function(T?) onChanged,
  }) => DropdownButtonFormField<T>(
    value: value,
    dropdownColor: AppTheme.bgPanel,
    style: const TextStyle(color: AppTheme.textMain, fontSize: 13),
    decoration: const InputDecoration(
      contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
    ),
    items: items.map((t) => DropdownMenuItem(value: t, child: Text(label(t)))).toList(),
    onChanged: onChanged,
  );
}
