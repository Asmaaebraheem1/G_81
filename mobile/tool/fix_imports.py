from pathlib import Path

root = Path("lib/features")
changed = []
for p in root.glob("*/presentation/*.dart"):
    text = p.read_text(encoding="utf-8")
    original = text
    feature = p.parent.parent.name
    if feature == "dashboard":
        text = text.replace(
            "import '../dashboard/data/carbon_repository.dart';",
            "import '../data/carbon_repository.dart';",
        )
        text = text.replace(
            "import '../auth/presentation/auth_cubit.dart';",
            "import '../../auth/presentation/auth_cubit.dart';",
        )
    else:
        text = text.replace("import '../../core/", "import '../../../core/")
        text = text.replace(
            "import '../dashboard/data/", "import '../../dashboard/data/"
        )
    if p.name == "settings_page.dart":
        if "import 'settings_cubit.dart';" not in text:
            text = text.replace(
                "import '../../dashboard/data/carbon_repository.dart';",
                "import '../../dashboard/data/carbon_repository.dart';\nimport 'settings_cubit.dart';",
            )
    if text != original:
        p.write_text(text, encoding="utf-8")
        changed.append(str(p).replace("\\", "/"))

auth_repo = Path("lib/features/auth/data/auth_repository.dart")
text = auth_repo.read_text(encoding="utf-8")
text = text.replace("import '../network/", "import '../../../core/network/")
text = text.replace("import '../storage/", "import '../../../core/storage/")
text = text.replace("import '../models.dart';", "import '../../../core/models.dart';")
auth_repo.write_text(text, encoding="utf-8")

print("changed:", len(changed))
for item in changed:
    print(item)
