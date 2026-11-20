import 'dart:convert';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// Offline read cache. The API remains authoritative; writes always go remote.
class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();
  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    final directory = await getDatabasesPath();
    _db = await openDatabase(
      p.join(directory, 'carbonwise_cache.db'),
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE cache_entries (
            bucket TEXT NOT NULL,
            item_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (bucket, item_id)
          )
        ''');
      },
    );
    return _db!;
  }

  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}

class LocalCache {
  LocalCache({AppDatabase? database}) : _database = database ?? AppDatabase.instance;

  final AppDatabase _database;

  Future<void> put(String bucket, String id, Object? payload) async {
    final db = await _database.database;
    await db.insert(
      'cache_entries',
      {
        'bucket': bucket,
        'item_id': id,
        'payload_json': jsonEncode(payload),
        'fetched_at': DateTime.now().toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> putMany(String bucket, Map<String, Object?> items) async {
    final db = await _database.database;
    final batch = db.batch();
    final now = DateTime.now().toUtc().toIso8601String();
    for (final entry in items.entries) {
      batch.insert(
        'cache_entries',
        {
          'bucket': bucket,
          'item_id': entry.key,
          'payload_json': jsonEncode(entry.value),
          'fetched_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<dynamic> read(String bucket, String id) async {
    final db = await _database.database;
    final rows = await db.query(
      'cache_entries',
      where: 'bucket = ? AND item_id = ?',
      whereArgs: [bucket, id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return jsonDecode(rows.first['payload_json'] as String);
  }

  Future<dynamic> readBucket(String bucket) async {
    final db = await _database.database;
    final rows = await db.query(
      'cache_entries',
      where: 'bucket = ?',
      whereArgs: [bucket],
      orderBy: 'fetched_at DESC',
    );
    return rows
        .map((row) => jsonDecode(row['payload_json'] as String))
        .toList(growable: false);
  }

  Future<void> clear() async {
    final db = await _database.database;
    await db.delete('cache_entries');
  }
}
