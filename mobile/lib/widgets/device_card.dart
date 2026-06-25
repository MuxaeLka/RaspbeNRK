import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/device.dart';
import '../theme/app_theme.dart';

// ── Налаштування свічення (зберігаються в Device) ─────────────────
// glowColor і glowWidth додаємо як поля до Device через extension
extension DeviceGlow on Device {
  // Дефолти — зелений, ширина 12
  Color get resolvedGlowColor {
    if (glowColorHex != null) {
      try {
        return Color(int.parse(glowColorHex!.replaceFirst('#', '0xFF')));
      } catch (_) {}
    }
    return online == true ? AppTheme.online : AppTheme.offline;
  }

  double get resolvedGlowWidth => glowWidth ?? 12.0;
}

// ── Іконки типів ──────────────────────────────────────────────────
IconData deviceTypeIcon(DeviceType t) {
  switch (t) {
    case DeviceType.raspberry: return Icons.developer_board;
    case DeviceType.mikrotik:  return Icons.router;
    case DeviceType.custom:    return Icons.settings_ethernet;
  }
}

// ── Картка пристрою ───────────────────────────────────────────────
class DeviceCard extends StatelessWidget {
  final Device device;
  final VoidCallback onDoubleTap;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final VoidCallback onCheck;

  const DeviceCard({
    super.key,
    required this.device,
    required this.onDoubleTap,
    required this.onEdit,
    required this.onDelete,
    required this.onCheck,
  });

  void _showContextMenu(BuildContext context) {
    HapticFeedback.mediumImpact();
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgPanel,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        side: BorderSide(color: AppTheme.border),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle
            Container(
              margin: const EdgeInsets.symmetric(vertical: 10),
              width: 36, height: 4,
              decoration: BoxDecoration(
                color: AppTheme.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            // Заголовок
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Row(children: [
                _GlowIcon(device: device, size: 32),
                const SizedBox(width: 12),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(device.name,
                    style: const TextStyle(color: AppTheme.textMain,
                        fontSize: 15, fontWeight: FontWeight.w700)),
                  Text('${device.ip}:${device.port}',
                    style: const TextStyle(color: AppTheme.textDim, fontSize: 11,
                        fontFamily: 'monospace')),
                ]),
              ]),
            ),
            const Divider(color: AppTheme.border, height: 1),
            _item(context, Icons.refresh,         'Перевірити',       AppTheme.textMain,  onCheck),
            _item(context, Icons.open_in_browser, 'Відкрити веб',     AppTheme.accent,    onDoubleTap),
            _item(context, Icons.edit_outlined,   'Редагувати',       AppTheme.textMain,  onEdit),
            _item(context, Icons.delete_outline,  'Видалити',         AppTheme.offline,   onDelete),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Widget _item(BuildContext ctx, IconData icon, String label, Color color, VoidCallback action) =>
    ListTile(
      leading: Icon(icon, color: color, size: 22),
      title: Text(label, style: TextStyle(color: color, fontSize: 14)),
      onTap: () { Navigator.pop(ctx); action(); },
    );

  String get _statusText {
    if (device.online == null) return '···';
    if (device.online!)        return device.pingMs != null ? '${device.pingMs} мс' : 'OK';
    return 'OFF';
  }

  Color get _statusColor {
    if (device.online == null) return AppTheme.textDim;
    return device.online! ? AppTheme.online : AppTheme.offline;
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onDoubleTap:  onDoubleTap,
      onLongPress:  () => _showContextMenu(context),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 400),
        decoration: BoxDecoration(
          color:        AppTheme.bgCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: device.online == true
                ? device.resolvedGlowColor.withOpacity(0.5)
                : device.online == false
                    ? AppTheme.offline.withOpacity(0.3)
                    : AppTheme.border,
            width: 1.5,
          ),
          boxShadow: device.online == true
              ? [BoxShadow(
                  color:       device.resolvedGlowColor.withOpacity(0.25),
                  blurRadius:  device.resolvedGlowWidth,
                  spreadRadius: device.resolvedGlowWidth / 6,
                )]
              : device.online == false
                  ? [BoxShadow(
                      color:      AppTheme.offline.withOpacity(0.12),
                      blurRadius: 8,
                    )]
                  : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // ── Іконка з анімованим свіченням ────────────────────
            _GlowIcon(device: device, size: 52),

            const SizedBox(height: 8),

            // ── Назва ─────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Text(
                device.name,
                style: const TextStyle(
                  color: AppTheme.textMain,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
                textAlign: TextAlign.center,
                overflow: TextOverflow.ellipsis,
              ),
            ),

            const SizedBox(height: 2),

            // ── Статус ────────────────────────────────────────────
            Text(
              _statusText,
              style: TextStyle(
                color: _statusColor,
                fontSize: 10,
                fontWeight: FontWeight.w600,
              ),
            ),

            const SizedBox(height: 1),

            // ── IP ────────────────────────────────────────────────
            Text(
              device.ip,
              style: const TextStyle(
                color: AppTheme.textDim,
                fontSize: 9,
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
      ),
    ).animate(key: ValueKey('${device.id}_${device.online}')).fadeIn(duration: 250.ms);
  }
}

// ── Іконка з пульсуючим свіченням по контуру ─────────────────────
class _GlowIcon extends StatefulWidget {
  final Device device;
  final double size;
  const _GlowIcon({required this.device, required this.size});

  @override
  State<_GlowIcon> createState() => _GlowIconState();
}

class _GlowIconState extends State<_GlowIcon> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double>   _pulse;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);
    _pulse = CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut);
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final d          = widget.device;
    final isOnline   = d.online == true;
    final isOffline  = d.online == false;
    final glowColor  = d.resolvedGlowColor;
    final glowWidth  = d.resolvedGlowWidth;
    final iconColor  = isOnline ? glowColor : isOffline ? AppTheme.offline : AppTheme.textDim;
    final iconSize   = widget.size * 0.5;

    return AnimatedBuilder(
      animation: _pulse,
      builder: (_, __) {
        final opacity = isOnline
            ? 0.3 + _pulse.value * 0.55   // 0.3 → 0.85 плавно
            : isOffline
                ? 0.15 + _pulse.value * 0.1
                : 0.0;

        return Container(
          width:  widget.size,
          height: widget.size,
          decoration: BoxDecoration(
            shape:  BoxShape.circle,
            color:  iconColor.withOpacity(0.08),
            border: Border.all(
              color: iconColor.withOpacity(isOnline ? 0.4 : 0.2),
              width: 1.5,
            ),
            // Свічення повторює контур кола — blur + spread
            boxShadow: [
              BoxShadow(
                color:       glowColor.withOpacity(opacity),
                blurRadius:  glowWidth,
                spreadRadius: glowWidth * 0.15,
              ),
              if (isOnline)
                BoxShadow(
                  color:       glowColor.withOpacity(opacity * 0.4),
                  blurRadius:  glowWidth * 2.5,
                  spreadRadius: 0,
                ),
            ],
          ),
          child: Icon(deviceTypeIcon(d.deviceType), color: iconColor, size: iconSize),
        );
      },
    );
  }
}
