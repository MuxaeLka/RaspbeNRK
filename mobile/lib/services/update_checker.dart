import 'dart:convert';
import 'package:http/http.dart' as http;

class UpdateInfo {
  final String version;
  final String url;
  final String body;
  UpdateInfo({required this.version, required this.url, required this.body});
}

class UpdateChecker {
  static const _repo = 'MuxaeLka/RaspbeNRK';
  static const _apiUrl = 'https://api.github.com/repos/$_repo/releases/latest';
  static const _currentVersion = '1.0.0';

  static Future<UpdateInfo?> checkForUpdate() async {
    try {
      final res = await http
          .get(Uri.parse(_apiUrl), headers: {'Accept': 'application/vnd.github.v3+json'})
          .timeout(const Duration(seconds: 5));

      if (res.statusCode != 200) return null;
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final tag  = (data['tag_name'] as String).replaceAll('v', '').trim();
      final url  = data['html_url']  as String? ?? 'https://github.com/$_repo/releases/latest';
      final body = data['body']      as String? ?? '';

      if (_isNewer(tag, _currentVersion)) {
        return UpdateInfo(version: tag, url: url, body: body);
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  static bool _isNewer(String remote, String current) {
    final r = _parse(remote);
    final c = _parse(current);
    for (int i = 0; i < 3; i++) {
      if (r[i] > c[i]) return true;
      if (r[i] < c[i]) return false;
    }
    return false;
  }

  static List<int> _parse(String v) {
    final parts = v.split('.');
    return List.generate(3, (i) => i < parts.length ? int.tryParse(parts[i]) ?? 0 : 0);
  }
}
