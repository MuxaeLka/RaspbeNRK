import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../models/device.dart';
import '../theme/app_theme.dart';

class WebViewScreen extends StatefulWidget {
  final Device device;
  const WebViewScreen({super.key, required this.device});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late final WebViewController _ctrl;
  bool   _loading  = true;
  bool   _hasError = false;
  int    _progress = 0;
  String _title    = '';

  @override
  void initState() {
    super.initState();
    _title = widget.device.name;

    _ctrl = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(AppTheme.bgDeep)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) {
          setState(() { _loading = true; _hasError = false; });
        },
        onPageFinished: (url) async {
          final t = await _ctrl.getTitle();
          setState(() {
            _loading = false;
            _title   = (t?.isNotEmpty == true) ? t! : widget.device.name;
          });
        },
        onProgress: (p) => setState(() => _progress = p),
        onWebResourceError: (err) {
          setState(() { _loading = false; _hasError = true; });
        },
        onHttpError: (err) {
          if ((err.response?.statusCode ?? 0) >= 500) {
            setState(() { _loading = false; _hasError = true; });
          }
        },
      ))
      ..loadRequest(Uri.parse(widget.device.webUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgDeep,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_title,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
              overflow: TextOverflow.ellipsis,
            ),
            Text(widget.device.webUrl,
              style: const TextStyle(fontSize: 10, color: AppTheme.textDim),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: () {
              setState(() { _loading = true; _hasError = false; });
              _ctrl.reload();
            },
          ),
          IconButton(
            icon: const Icon(Icons.arrow_back_ios, size: 18),
            onPressed: () async {
              if (await _ctrl.canGoBack()) _ctrl.goBack();
            },
          ),
          IconButton(
            icon: const Icon(Icons.arrow_forward_ios, size: 18),
            onPressed: () async {
              if (await _ctrl.canGoForward()) _ctrl.goForward();
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          if (_hasError)
            _buildError()
          else
            WebViewWidget(controller: _ctrl),

          // Прогрес-бар
          if (_loading && !_hasError)
            Positioned(
              top: 0, left: 0, right: 0,
              child: LinearProgressIndicator(
                value: _progress > 0 ? _progress / 100 : null,
                backgroundColor: AppTheme.bgPanel,
                valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.accent),
                minHeight: 2,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildError() => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.wifi_off, size: 64, color: AppTheme.offline),
        const SizedBox(height: 16),
        Text(
          'Не вдалося підключитись до\n${widget.device.webUrl}',
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppTheme.textDim, fontSize: 13),
        ),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          icon: const Icon(Icons.refresh, size: 16),
          label: const Text('Повторити'),
          onPressed: () {
            setState(() { _loading = true; _hasError = false; });
            _ctrl.reload();
          },
        ),
      ],
    ),
  );
}
