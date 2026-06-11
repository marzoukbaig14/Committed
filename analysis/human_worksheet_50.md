# Committed — human rating worksheet

50 examples. Rate each on the four axes, **pass** or **fail**, using the rubric in `docs/eval/judge_rubric.md`. Rate only from the diff and the candidate below — the gold message and the judge's labels are deliberately hidden. type_correctness is plausibility-based (would a reviewer accept this type for this diff?), not match-to-gold.

Axes: type_correctness · faithfulness (hard gate) · completeness · specificity.

When done, copy each pass/fail into the matching id in the skeleton jsonl.

---

## 1 of 50  ·  id `2881`

**Diff**

```diff
#!/bin/bash
-CURRENT_LERNA_VERSION=$(node -p -e "require('./lerna.json').version")
-IS_IN_RC_STATUS=$(echo "${CURRENT_LERNA_VERSION}" | awk '/rc\.[0-9]+$/')
+git_hash=$(git rev-parse --short "$GITHUB_SHA")
-if [ ! -z "${IS_IN_RC_STATUS}" ]
-then
- echo "Current Version is already in release candidate status. Skipping snapshot release."
- exit 0
-fi
-
-${GITHUB_WORKSPACE}/node_modules/.bin/lerna publish prerelease \
- --canary \
- --conventional-prerelease \
+${GITHUB_WORKSPACE}/node_modules/.bin/lerna publish "0.0.0-${git_hash}" \
+ --no-push \
+ --no-git-tag-version \
--dist-tag dev \
- --preid dev
+

```

**Candidate message**

> feat(backend): Add support for publishing prerelease versions with custom version tags via GitHub Actions

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 2 of 50  ·  id `1486`

**Diff**

```diff
@@ -718,11 +718,10 @@ Band *pluto_get_parallel_band(Ploop *loop, PlutoProg *prog, int *innermost_split
/* Dependences satisfied outer to the band don't matter */
if (dep->satisfaction_level < loop->depth) continue;
/* The loop (or scalar dimension) has to be parallel */
- if (dep->dirvec[depth] != DEP_ZERO) break;
+ if (dep->satvec[depth]) break;
}
if (i<prog->ndeps) break;
depth++;
- // printf("Depth %d\n", depth);
}while (depth < prog->num_hyperplanes);
/* Peel off scalar dimensions from the end */

```

**Candidate message**

> feat(test): add check for saturation status in parallel band dependency check

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 3 of 50  ·  id `2220`

**Diff**

```diff
@@ -1192,14 +1192,24 @@ public bool IsOverlayVisible()
public void ShowOverlay()
{
- this.overlayBox?.SetCurrentValue(VisibilityProperty, Visibility.Visible);
- this.overlayBox?.SetCurrentValue(OpacityProperty, this.OverlayOpacity);
+ if (this.overlayBox is null)
+ {
+ return;
+ }
+
+ this.overlayBox.SetCurrentValue(VisibilityProperty, Visibility.Visible);
+ this.overlayBox.SetCurrentValue(OpacityProperty, this.OverlayOpacity);
}
public void HideOverlay()
{
- this.overlayBox?.SetCurrentValue(OpacityProperty, 0d);
- this.overlayBox?.SetCurrentValue(VisibilityProperty, Visibility.Hidden);
+ if (this.overlayBox is null)
+ {
+ return;
+ }
+
+ this.overlayBox.SetCurrentValue(OpacityProperty, 0d);
+ this.overlayBox.SetCurrentValue(VisibilityProperty, Visibility.Hidden);
}
/// <summary>
@@ -1208,18 +1218,18 @@ public void HideOverlay()
/// <param name="thisElement">The element which will be focused again.</param>
public void StoreFocus(IInputElement? thisElement = null)
{
- this.Dispatcher.BeginInvoke(new Action(() => { this.restoreFocus = thisElement ?? (this.restoreFocus ?? FocusManager.GetFocusedElement(this)); }));
+ this.BeginInvoke(() => { this.restoreFocus = thisElement ?? (this.restoreFocus ?? FocusManager.GetFocusedElement(this)); });
}
internal void RestoreFocus()
{
if (this.restoreFocus != null)
{
- this.Dispatcher.BeginInvoke(new Action(() =>
+ this.BeginInvoke(() =>
{
Keyboard.Focus(this.restoreFocus);
this.restoreFocus = null;
- }));
+ });
}
}

```

**Candidate message**

> feat(overlay): Add null check in `ShowOverlay` and `HideOverlay` to handle null `overlayBox` gracefully. 📦

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 4 of 50  ·  id `2477`

**Diff**

```diff
@@ -37,6 +37,16 @@ defmodule TimezoneTests do
assert %TimezoneInfo{} = Timezone.local()
end
+ test "creation/conversion/difference" do
+ datetime = ~U[2020-11-01T04:00:00Z]
+ tz = Timex.timezone("America/Los_Angeles", datetime)
+ zoned = Timex.to_datetime(datetime, "America/Los_Angeles")
+ assert zoned == Timex.Timezone.convert(datetime, "America/Los_Angeles")
+
+ shifted = DateTime.add(datetime, tz.offset_std)
+ assert Timex.diff(Timex.Timezone.convert(zoned, "Etc/UTC"), shifted, :second) == 0
+ end
+
property "convert always returns DateTime or AmbiguousDateTime" do
check all(
input_date <- PropertyHelpers.date_time_generator(:tuple),

```

**Candidate message**

> feat(tests): add test for timezone conversion difference functionality

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 5 of 50  ·  id `554`

**Diff**

```diff
@@ -14,6 +14,7 @@ xcodebuild -project Adyen.xcodeproj \
-scheme AdyenUIHost \
-destination="generic/platform=iOS" \
-sdk iphoneos \
+-allowProvisioningUpdates \
-configuration Release \
archive \
-archivePath $BUILD_PATH/AdyenUIHost.xcarchive

```

**Candidate message**

> feat(additional-option): add allowProvisioningUpdates to xcodebuild command

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 6 of 50  ·  id `2625`

**Diff**

```diff
+package jadx.tests.integration.arith;
+
+import org.junit.jupiter.api.Test;
+
+import jadx.NotYetImplemented;
+import jadx.tests.api.IntegrationTest;
+
+import static jadx.tests.api.utils.assertj.JadxAssertions.assertThat;
+
+public class TestSpecialValues2 extends IntegrationTest {
+
+ public static class TestCls {
+ private static int compareUnsigned(final int x, final int y) {
+ return Integer.compare(x + Integer.MIN_VALUE, y + Integer.MIN_VALUE);
+ }
+ }
+
+ @NotYetImplemented("Constant value replace")
+ @Test
+ public void test() {
+ noDebugInfo();
+ assertThat(getClassNode(TestCls.class))
+ .code()
+ .countString(2, "Integer.MIN_VALUE");
+ }
+}

```

**Candidate message**

> feat(tests): add missing implementation for "Constant value replace" test case

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 7 of 50  ·  id `2790`

**Diff**

```diff
@@ -58,6 +58,10 @@ class Workflow(Document):
docstatus_map[d.doc_status] = d.state
def update_doc_status(self):
+ '''
+ Checks if the docstatus of a state was updated.
+ If yes then the docstatus of the document with same state will be updated
+ '''
doc_before_save = self.get_doc_before_save()
before_save_states, new_states = {}, {}
if doc_before_save:
@@ -69,14 +73,12 @@ class Workflow(Document):
for key in new_states:
if key in before_save_states:
if not new_states[key].doc_status == before_save_states[key].doc_status:
- frappe.db.set_value(self.document_type,
- {
+ frappe.db.set_value(self.document_type, {
self.workflow_state_field: before_save_states[key].state
},
'docstatus',
new_states[key].doc_status,
- update_modified = False
- )
+ update_modified = False)
def validate_docstatus(self):
def get_state(state):

```

**Candidate message**

> feat(additional-docstring-and-logic): add documentation comment and update logic for `update_doc_status` method. 📝

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 8 of 50  ·  id `2026`

**Diff**

```diff
@@ -515,7 +515,6 @@ class RenderFlowLayout extends RenderLayoutBox {
if (isInlineBlock && constraints.maxWidth.isInfinite) {
for (int i = 0; i < _runMetrics.length; ++i) {
final _RunMetrics metrics = _runMetrics[i];
-
final Map<int?, RenderBox> runChildren = metrics.runChildren;
final List<RenderBox> runChildrenList = runChildren.values.toList();
@@ -526,9 +525,14 @@ class RenderFlowLayout extends RenderLayoutBox {
// Element of display block will stretch to the width of its container
// when its width is not specified.
if (isChildBlockLevel && child.constraints.maxWidth.isInfinite) {
+ double contentBoxWidth = renderStyle.contentBoxWidth!;
+ // No need to layout child when its width is identical to parent's width.
+ if (child.renderStyle.borderBoxWidth == contentBoxWidth) {
+ continue;
+ }
BoxConstraints childConstraints = BoxConstraints(
- minWidth: size.width,
- maxWidth: size.width,
+ minWidth: contentBoxWidth,
+ maxWidth: contentBoxWidth,
minHeight: child.constraints.minHeight,
maxHeight: child.constraints.maxHeight,
);

```

**Candidate message**

> feat(test): Add check for content box width equality in child layout

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 9 of 50  ·  id `2105`

**Diff**

```diff
@@ -138,7 +138,7 @@ internal unsafe T ReadBlittable<T>()
public byte ReadByte() => ReadBlittable<byte>();
/// <summary>Read 'count' bytes into the bytes array</summary>
- // TODO why does this also return bytes[]???
+ // NOTE: returns byte[] because all reader functions return something.
[MethodImpl(MethodImplOptions.AggressiveInlining)]
public byte[] ReadBytes(byte[] bytes, int count)
{
@@ -147,9 +147,14 @@ public byte[] ReadBytes(byte[] bytes, int count)
{
throw new EndOfStreamException($"ReadBytes can't read {count} + bytes because the passed byte[] only has length {bytes.Length}");
}
+ // check if within buffer limits
+ if (Position + count > buffer.Count)
+ {
+ throw new EndOfStreamException($"ReadBytesSegment can't read {count} bytes because it would read past the end of the stream. {ToString()}");
+ }
- ArraySegment<byte> data = ReadBytesSegment(count);
- Array.Copy(data.Array, data.Offset, bytes, 0, count);
+ Array.Copy(buffer.Array, buffer.Offset + Position, bytes, 0, count);
+ Position += count;
return bytes;
}

```

**Candidate message**

> feat(test): add note in ReadBytes to clarify return behavior

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 10 of 50  ·  id `210`

**Diff**

```diff
@@ -64,6 +64,10 @@ public function getClientEntity($clientIdentifier, $grantType = null,
*/
protected function handlesGrant($record, $grantType)
{
+ if (is_array($record->grant_types) && !in_array($grantType, $record->grant_types)) {
+ return false;
+ }
+
switch ($grantType) {
case 'authorization_code':
return ! $record->firstParty();

```

**Candidate message**

> feat(protected-method): Add check for grant type in handlesGrant()

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 11 of 50  ·  id `584`

**Diff**

```diff
@@ -41,7 +41,9 @@ pub mod builders {
#[cfg(any(test, feature = "abigen"))]
#[cfg_attr(docsrs, doc(cfg(feature = "abigen")))]
-pub use ethers_contract_abigen::{Abigen, MultiAbigen};
+pub use ethers_contract_abigen::{
+ Abigen, ContractFilter, ExcludeContracts, MultiAbigen, SelectContracts,
+};
#[cfg(any(test, feature = "abigen"))]
#[cfg_attr(docsrs, doc(cfg(feature = "abigen")))]

```

**Candidate message**

> feat(adds): add Abigen with additional traits

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: fail
- completeness: pass
- specificity: fail

---

## 12 of 50  ·  id `2879`

**Diff**

```diff
@@ -701,14 +701,6 @@ endmenu\n" >> ${IDF_PATH}/Kconfig
git checkout CMakeLists.txt
rm -f log.txt
- print_status "Compiles with dependencies delivered by component manager"
- clean_build_dir
- printf "\n#include \"test_component.h\"\n" >> main/main.c
- printf "dependencies:\n test_component:\n path: test_component\n git: ${COMPONENT_MANAGER_TEST_REPO}\n" >> main/idf_component.yml
- idf.py reconfigure build || failure "Build didn't succeed with required components installed by package manager"
- rm main/idf_component.yml
- git checkout main/main.c
-
print_status "Build fails if partitions don't fit in flash"
sed -i.bak "s/CONFIG_ESPTOOLPY_FLASHSIZE.\+//" sdkconfig # remove all flashsize config
echo "CONFIG_ESPTOOLPY_FLASHSIZE_1MB=y" >> sdkconfig # introduce undersize flash

```

**Candidate message**

> feat(additional-config): Add configuration for flash size control in ESP-IDF build process. ✅

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 13 of 50  ·  id `11`

**Diff**

```diff
@@ -35,17 +35,19 @@ export const updateExpectedMediaItems: (roId: string, slId: string) => void
})
function iterateOnSLILike (doc: SegmentLineItemGeneric, prefix: string) {
- if (doc.content && doc.content.fileName && doc.content.mediaFlowId) {
+ if (doc.content && doc.content.fileName && doc.content.mediaFlowIds) {
+ (doc.content.mediaFlowIds as string[]).forEach((flow) => {
eMIs.push(literal<ExpectedMediaItem>({
- _id: prefix + '_' + doc._id,
+ _id: prefix + '_' + doc._id + '_' + flow,
disabled: false,
lastSeen: getCurrentTime(),
- mediaFlowId: doc.content.mediaFlowId as string,
- path: doc.content.fileName as string,
+ mediaFlowId: flow,
+ path: this.toString(),
runningOrderId: roId,
segmentLineId: slId
}))
+ }, doc.content.fileName)
}
}

```

**Candidate message**

> feat(test): Add support for iterating over media flow IDs in `updateExpectedMediaItems` function. 📦

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 14 of 50  ·  id `2118`

**Diff**

```diff
@@ -190,11 +190,10 @@ object PackageUtils {
* @return List of LibStringItem
*/
private fun getSourceLibs(path: String, childDir: String, source: String? = null): List<LibStringItem> {
- var zipFile: ZipFile? = null
-
try {
val file = File(path)
- zipFile = ZipFile(file)
+ val zipFile = ZipFile(file)
+ zipFile.use {
val entries = zipFile.entries()
val libList = entries.asSequence()
.filter { (it.name.contains(childDir)) && it.name.endsWith(".so") }
@@ -207,11 +206,10 @@ object PackageUtils {
}
return libList
+ }
} catch (e: Exception) {
loge(e.toString())
return emptyList()
- } finally {
- zipFile?.close()
}
}
@@ -280,22 +278,20 @@ object PackageUtils {
* @return true if it uses Kotlin language
*/
fun isKotlinUsed(packageInfo: PackageInfo): Boolean {
- var zipFile: ZipFile? = null
-
return try {
val path = packageInfo.applicationInfo.sourceDir
val file = File(path)
- zipFile = ZipFile(file)
+ val zipFile = ZipFile(file)
+ zipFile.use {
if (zipFile.entries().asSequence().any { it.name.startsWith("kotlin/") || it.name.startsWith("META-INF/services/kotlin") }) {
true
} else {
isKotlinUsedInClassDex(file)
}
+ }
} catch (e: Exception) {
false
- } finally {
- zipFile?.close()
}
}
@@ -306,7 +302,9 @@ object PackageUtils {
*/
private fun isKotlinUsedInClassDex(file: File): Boolean {
return try {
- ApkFile(file).dexClasses.asSequence().any { it.toString().startsWith("Lkotlin/") || it.toString().startsWith("Lkotlinx/") }
+ ApkFile(file).use { apkFile ->
+ apkFile.dexClasses.asSequence().any { it.toString().startsWith("Lkotlin/") || it.toString().startsWith("Lkotlinx/") }
+ }
} catch (e: Exception) {
false
}
@@ -452,11 +450,14 @@ object PackageUtils {
var elementName: String
val file = File(path)
- val zipFile = ZipFile(file)
- val entries = zipFile.entries()
- val apkFile = ApkFile(file)
+ var zipFile: ZipFile? = null
+ var apkFile: ApkFile? = null
try {
+ zipFile = ZipFile(file)
+ val entries = zipFile.entries()
+ apkFile = ApkFile(file)
+
if (apkFile.manifestXml.contains("use32bitAbi=\"true\"", true)) {
abi = when {
GlobalValues.deviceSupportedAbis.contains(ARMV7_STRING) -> ARMV7
@@ -511,7 +512,8 @@ object PackageUtils {
loge(e.toString())
return ERROR
} finally {
- zipFile.close()
+ zipFile?.close()
+ apkFile?.close()
}
}
@@ -614,8 +616,9 @@ object PackageUtils {
if (path.isNullOrEmpty()) {
return false
}
- val apkFile = ApkFile(File(path))
+ ApkFile(File(path)).use { apkFile ->
return apkFile.dexClasses.any { it.packageName.startsWith(dexClassPrefix) }
+ }
} catch (e: Exception) {
return false
}
@@ -639,9 +642,9 @@ object PackageUtils {
if (path.isNullOrEmpty()) {
return emptyList()
}
- val apkFile = ApkFile(File(path))
var splits: List<String>
+ ApkFile(File(path)).use { apkFile ->
val primaryList = apkFile.dexClasses
.map { it.packageName }
.filter { !it.startsWith(packageName) }
@@ -685,6 +688,7 @@ object PackageUtils {
}
}
return primaryList
+ }
} catch (e: Exception) {
loge(e.toString())
return emptyList()
@@ -712,8 +716,9 @@ object PackageUtils {
*/
fun isIntelCpu(): Boolean {
return try {
- BufferedReader(FileReader("/proc/cpuinfo"))
- .readLine().contains("Intel")
+ BufferedReader(FileReader("/proc/cpuinfo")).use {
+ it.readLine().contains("Intel")
+ }
} catch (e: Exception) {
false
}

```

**Candidate message**

> feat(additional-code): Add support for checking Intel CPU in `isIntelCpu()` function

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 15 of 50  ·  id `2431`

**Diff**

```diff
// limitations under the License.
#include "google/cloud/spanner/mutations.h"
+#include "google/cloud/spanner/bytes.h"
+#include "google/cloud/spanner/date.h"
+#include "google/cloud/spanner/json.h"
#include "google/cloud/spanner/keys.h"
+#include "google/cloud/spanner/numeric.h"
+#include "google/cloud/spanner/timestamp.h"
#include "google/cloud/testing_util/is_proto_equal.h"
#include "absl/types/optional.h"
#include <google/protobuf/text_format.h>
@@ -318,6 +323,43 @@ TEST(MutationsTest, DeleteSimple) {
EXPECT_THAT(actual, IsProtoEqual(expected));
}
+TEST(MutationsTest, SpannerTypes) {
+ Mutation empty;
+ auto bytes = Bytes("bytes");
+ auto date = Date(2022, 3, 30);
+ auto json = Json("{true}");
+ auto numeric = MakeNumeric(42).value();
+ auto timestamp = Timestamp();
+ Mutation insert = MakeInsertMutation( //
+ "table-name", //
+ {"bytes", "date", "json", "numeric", "timestamp"}, //
+ bytes, date, json, numeric, timestamp);
+ EXPECT_EQ(insert, insert);
+ EXPECT_NE(insert, empty);
+
+ auto actual = std::move(insert).as_proto();
+ auto constexpr kText = R"pb(
+ insert {
+ table: "table-name"
+ columns: "bytes"
+ columns: "date"
+ columns: "json"
+ columns: "numeric"
+ columns: "timestamp"
+ values {
+ values { string_value: "Ynl0ZXMA" }
+ values { string_value: "2022-03-30" }
+ values { string_value: "{true}" }
+ values { string_value: "42" }
+ values { string_value: "1970-01-01T00:00:00Z" }
+ }
+ }
+ )pb";
+ google::spanner::v1::Mutation expected;
+ ASSERT_TRUE(TextFormat::ParseFromString(kText, &expected));
+ EXPECT_THAT(actual, IsProtoEqual(expected));
+}
+
TEST(MutationsTest, FluentInsertBuilder) {
static_assert(
std::is_rvalue_reference<decltype(std::declval<InsertMutationBuilder>()

```

**Candidate message**

> style(adds/include-statements): add include statements for spanner types

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 16 of 50  ·  id `2484`

**Diff**

```diff
@@ -7,6 +7,7 @@ import (
"os"
"os/exec"
"path/filepath"
+ "runtime"
"strconv"
"strings"
"testing"
@@ -49,7 +50,15 @@ func TestYaegiCmdCancel(t *testing.T) {
}()
yaegi := filepath.Join(tmp, "yaegi")
- build := exec.Command("go", "build", "-race", "-o", yaegi, ".")
+
+ args := []string{"build"}
+ if raceDetectorSupported(runtime.GOOS, runtime.GOARCH) {
+ args = append(args, "-race")
+ }
+ args = append(args, "-o", yaegi, ".")
+
+ build := exec.Command("go", args...)
+
out, err := build.CombinedOutput()
if err != nil {
t.Fatalf("failed to build yaegi command: %v: %s", err, out)
@@ -115,3 +124,16 @@ func TestYaegiCmdCancel(t *testing.T) {
}
}
}
+
+func raceDetectorSupported(goos, goarch string) bool {
+ switch goos {
+ case "linux":
+ return goarch == "amd64" || goarch == "ppc64le" || goarch == "arm64"
+ case "darwin":
+ return goarch == "amd64" || goarch == "arm64"
+ case "freebsd", "netbsd", "openbsd", "windows":
+ return goarch == "amd64"
+ default:
+ return false
+ }
+}

```

**Candidate message**

> feat(backend): add race detector support in build system

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 17 of 50  ·  id `2616`

**Diff**

```diff
@@ -16,10 +16,15 @@ namespace Unity.Netcode.RuntimeTests
private void Update()
{
+ // Since the local position is transformed from local to global and vice-versa on the server and client
+ // it may accumulate some error. We allow an error of 0.01 over the range of 1000 used in this test.
+ // This requires precision to 5 digits, so it doesn't weaken the test, while preventing spurious failures
+ const float maxRoundingError = 0.01f;
+
// Check the position of the nested object on the client
if (CheckPosition)
{
- if (transform.position.y < 0.0f || transform.position.y > 100.0f)
+ if (transform.position.y < -maxRoundingError || transform.position.y > 100.0f + maxRoundingError)
{
Debug.LogError($"Interpolation failure. transform.position.y is {transform.position.y}. Should be between 0.0 and 100.0");
}

```

**Candidate message**

> feat(test): Add tolerance for position check in interpolation test

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 18 of 50  ·  id `2827`

**Diff**

```diff
@@ -148,7 +148,7 @@ BlueprintImpl
BlueprintImpl::ComponentNamesType
BlueprintImpl
-::GetComponentNames( void ) const
+::GetComponentNames() const
{
ComponentNamesType container;
for( auto it = boost::vertices( this->m_Graph.graph() ).first; it != boost::vertices( this->m_Graph.graph() ).second; ++it )
@@ -528,7 +528,6 @@ BlueprintImpl::MergeFromFile(const std::string & fileNameString)
}
this->m_LoggerImpl->Log(LogLevel::INF, "Checking {0} for include files ... done", fileName);
this->MergeProperties(propertyTree);
- return;
}
void

```

**Candidate message**

> feat(blueprintimpl-componentnames-type): Add `GetComponentNames()` method to `BlueprintImpl` to retrieve component names. ✅

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 19 of 50  ·  id `2863`

**Diff**

```diff
@@ -32,8 +32,8 @@ if [[ -n "${COMMIT_TAG}" ]]; then
# For versions we replace the version number v2.3.1 to v2-3-1
export BRANCH_HASH=$( printf "${COMMIT_TAG}" | sed "s/\./-/g" );
export IMAGE_TAG=$(printf "${COMMIT_TAG}" | sed "s/^v//")
- export ES_INDEX_PREFIX="cdtn-${BRANCH_HASH}"
- export K8S_NAMESPACE="cdtn-${BRANCH_HASH}"
+ export ES_INDEX_PREFIX="cdtn-preprod"
+ export K8S_NAMESPACE="cdtn-preprod"
fi
@@ -41,6 +41,7 @@ fi
if [[ -n "${PRODUCTION+x}" ]]; then
export BRANCH_HASH=prod;
export ES_INDEX_PREFIX="cdtn-prod"
+ export K8S_NAMESPACE="cdtn"
export DOMAIN="code.travail.fabrique.social.gouv.fr";
else
export DOMAIN="${BRANCH_HASH}-code-travail.dev.fabrique.social.gouv.fr";

```

**Candidate message**

> feat(features): Add environment variables for preprod and prod environments, update index prefix and namespace. 📦

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 20 of 50  ·  id `2857`

**Diff**

```diff
@@ -10,7 +10,7 @@ fi
./RootStock-NG.sh -c octavo-debian-buster-console-v4.19
./RootStock-NG.sh -c bb.org-debian-bullseye-console-v5.10-ti-armhf
./RootStock-NG.sh -c bb.org-debian-bullseye-console-arm64
-./RootStock-NG.sh -c bb.org-debian-sid-console-riscv64
+#./RootStock-NG.sh -c bb.org-debian-sid-console-riscv64
if [ -d ./ignore ] ; then
sudo rm -rf ./ignore || true

```

**Candidate message**

> feat(additional-console-configurations): Add support for new Debian release configurations in RootStock-NG. Update the script to include `-c bb.org-debian-sid-console-riscv64` and remove the unused `ignore` directory cleanup. 📦

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 21 of 50  ·  id `2225`

**Diff**

```diff
@@ -12,19 +12,19 @@ namespace Flextype;
use Bnf\Slim3Psr15\CallableResolver;
use Cocur\Slugify\Slugify;
use Flextype\App\Foundation\Cache\Cache;
+use Flextype\App\Foundation\Config;
+use Flextype\App\Foundation\Cors;
+use Flextype\App\Foundation\Entries\Entries;
use Flextype\App\Foundation\Media\MediaFiles;
use Flextype\App\Foundation\Media\MediaFilesMeta;
use Flextype\App\Foundation\Media\MediaFolders;
use Flextype\App\Foundation\Media\MediaFoldersMeta;
-use Flextype\App\Foundation\Entries\Entries;
use Flextype\App\Foundation\Plugins;
-use Flextype\App\Foundation\Cors;
-use Flextype\App\Foundation\Config;
use Flextype\App\Support\Parsers\Markdown;
use Flextype\App\Support\Parsers\Shortcode;
-use Flextype\App\Support\Serializers\Yaml;
-use Flextype\App\Support\Serializers\Json;
use Flextype\App\Support\Serializers\Frontmatter;
+use Flextype\App\Support\Serializers\Json;
+use Flextype\App\Support\Serializers\Yaml;
use Intervention\Image\ImageManager;
use League\Event\Emitter;
use League\Flysystem\Adapter\Local;
@@ -51,9 +51,7 @@ use Monolog\Logger;
use ParsedownExtra;
use Thunder\Shortcode\ShortcodeFacade;
use function date;
-use function dump;
use function extension_loaded;
-use function ucfirst;
/**
* Supply a custom callable resolver, which resolves PSR-15 middlewares.
@@ -126,7 +124,7 @@ $flextype['cache_adapter'] = function ($container) use ($flextype) {
'memcached' => 'Memcached',
'redis' => 'Redis',
'sqlite3' => 'SQLite3',
- 'zenddatacache' => 'ZendDataCache'
+ 'zenddatacache' => 'ZendDataCache',
];
$class_name = $drivers_classes[$driver_name];

```

**Candidate message**

> feat(plugins): Add `zenddatacache` adapter to Flextype configuration. 📦

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 22 of 50  ·  id `2784`

**Diff**

```diff
@@ -27,7 +27,7 @@ exports['HeaderCheckerLint opened pull request sets a "failure" context on PR, i
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/WrongYear.java` should have a copyright year of 2020"
+ "text": "`oauth2_http/java/com/google/auth/http/WrongYear.java` should have a copyright year of 2021"
}
}
@@ -49,7 +49,7 @@ exports['HeaderCheckerLint opened pull request sets a "failure" context on PR, i
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/InvalidCopyright.java` has an invalid copyright holder: `Invalid Holder`\n`oauth2_http/java/com/google/auth/http/InvalidCopyright.java` should have a copyright year of 2020"
+ "text": "`oauth2_http/java/com/google/auth/http/InvalidCopyright.java` has an invalid copyright holder: `Invalid Holder`\n`oauth2_http/java/com/google/auth/http/InvalidCopyright.java` should have a copyright year of 2021"
}
}
@@ -60,7 +60,7 @@ exports['HeaderCheckerLint opened pull request reads a custom configuration file
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/InvalidCopyright.java` should have a copyright year of 2020"
+ "text": "`oauth2_http/java/com/google/auth/http/InvalidCopyright.java` should have a copyright year of 2021"
}
}
@@ -71,7 +71,7 @@ exports['HeaderCheckerLint opened pull request ignores a valid license 1'] = {
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/NewFile2.java` should have a copyright year of 2020"
+ "text": "`oauth2_http/java/com/google/auth/http/NewFile2.java` should have a copyright year of 2021"
}
}
@@ -93,7 +93,7 @@ exports['HeaderCheckerLint opened pull request ignores copyright strings in the
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/CopyrightString.java` should have a copyright year of 2020"
+ "text": "`oauth2_http/java/com/google/auth/http/CopyrightString.java` should have a copyright year of 2021"
}
}
@@ -126,7 +126,7 @@ exports['HeaderCheckerLint updated pull request sets a "failure" context on PR,
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/WrongYear.java` should have a copyright year of 2020"
+ "text": "`oauth2_http/java/com/google/auth/http/WrongYear.java` should have a copyright year of 2021"
}
}
@@ -159,7 +159,7 @@ exports['HeaderCheckerLint updated pull request ignores a valid license 1'] = {
"output": {
"title": "Invalid or missing license headers detected.",
"summary": "Some new files are missing headers",
- "text": "`oauth2_http/java/com/google/auth/http/NewFile2.java` should have a copyright year of 2021"
+ "text": "`oauth2_http/java/com/google/auth/http/NewFile2.java` should have a copyright year of 2021"
}
}

```

**Candidate message**

> feat(additional-license-headers): Update text in HeaderCheckerLint to use 2021 year for all files missing license headers. 📄

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 23 of 50  ·  id `2851`

**Diff**

```diff
@@ -102,8 +102,18 @@ function run_plugin() {
"${PYTHON}" -m coverage run setup.py test 2>&1 | tee "${check_skips}"
"${PYTHON}" -m coverage report -m
- # Fail if any tests were skipped
- grep -v -q -E '(skipped=.*)' "${check_skips}"
+ # Fail if any tests were skipped or errored
+ skipped=$(grep -E '(skipped=.*)' "${check_skips}" | wc -l)
+ if [ "$skipped" -ne 0 ]; then
+ echo "Tests were skipped" >&2
+ exit 1
+ fi
+
+ errors=$(grep -E '(errors=.*)' "${check_skips}" | wc -l)
+ if [ "$errors" -ne 0 ]; then
+ echo "Tests errored" >&2
+ exit 1
+ fi
fi
if [ "x${GITHUB_ACTIONS}" == "xtrue" ] && [ "x${GITHUB_REF}" == "xrefs/heads/master" ]; then

```

**Candidate message**

> feat(add-checks): Add checks for skipped and errored tests in `run_plugin()`

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 24 of 50  ·  id `1711`

**Diff**

```diff
@@ -13,11 +13,6 @@ import SDWebImageSwiftUI
struct ContentView: View, StoreAccessor {
@EnvironmentObject var store: Store
- @State private var geoTimer = Timer.publish(
- every: 0.5, on: .current, in: .common
- )
- .autoconnect()
-
@State private var position: CGFloat = 0
@State private var aspectBox = [Int: CGFloat]()
@@ -58,12 +53,11 @@ struct ContentView: View, StoreAccessor {
ScrollView {
GeometryReader { geoProxy in
Text("I'm invisible~")
- .onReceive(geoTimer) { _ in
- updateGeoProxyMinY(
- geoProxy.frame(in: .global).minY
+ .onChange(
+ of: geoProxy.frame(in: .global).minY,
+ perform: updateGeoProxyMinY
)
}
- }
.frame(width: 0, height: 0)
LazyVStack(spacing: 0) {
ForEach(contents) { item in
@@ -73,10 +67,7 @@ struct ContentView: View, StoreAccessor {
retryLimit: setting.contentRetryLimit,
onSuccessAction: onWebImageSuccess
)
- .frame(
- width: screenW,
- height: calImageHeight(item.tag)
- )
+ .frame(height: calImageHeight(item.tag))
.onAppear {
onWebImageAppear(item)
}

```

**Candidate message**

> feat(additional-update): add `.onChange` to update geo proxy height based on image height

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 25 of 50  ·  id `2746`

**Diff**

```diff
@@ -140,8 +140,7 @@ export class PluginRegistry {
private async load(pluginMetaData: IPluginMetaData) {
this.validateMetaData(pluginMetaData);
- // Use `devUrl` from the manifest, if it exists.
- // This will be the case during local development.
+ // Use `url` from the manifest, if it exists. This will be the case during local development.
const { devUrl, url } = pluginMetaData;
const gateUrl = `${API.baseUrl}/plugins/deck/${pluginMetaData.id}/${pluginMetaData.version}/index.js`;
const pluginUrl = url ?? devUrl ?? gateUrl;

```

**Candidate message**

> feat(xd-registry-plugin): Use `url` from the manifest instead of `devUrl` in `PluginRegistry#load`

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 26 of 50  ·  id `2772`

**Diff**

```diff
@@ -25,14 +25,11 @@ lerna version \
--allow-branch latest \
--create-release github \
-m "chore(publish): latest" \
- --ignore-changes '**/*.md' '**/*.test.tsx?' '**/package-lock.json' '**/tsconfig.json'
+ --ignore-changes '**/*.md' '**/*.test.tsx?' '**/package-lock.json' '**/tsconfig.json'A
# 5. Publish to NPM
lerna publish from-package --yes
-# 6. Push CHANGELOGs and tags to GitHub
-git push && git push --tags
-
# 7. Backmerge to master
git checkout master
git merge latest

```

**Candidate message**

> feat(publish): add --ignore-changes option for publish command

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 27 of 50  ·  id `2748`

**Diff**

```diff
@@ -66,7 +66,7 @@ export type ExtendedListQueryOptions<T extends VendureEntity> = {
*
* Example: we want to allow sort/filter by and Order's `customerLastName`. The actual lastName property is
* not a column in the Order table, it exists on the Customer entity, and Order has a relation to Customer via
- * `Order.customer`. Therefore we can define a customPropertyMap like this:
+ * `Order.customer`. Therefore, we can define a customPropertyMap like this:
*
* @example
* ```GraphQL
@@ -90,7 +90,11 @@ export type ExtendedListQueryOptions<T extends VendureEntity> = {
* customPropertyMap: {
* // Tell TypeORM how to map that custom
* // sort/filter field to the property on a
- * // related entity
+ * // related entity. Note that the `customer`
+ * // part needs to match the *table name* of the
+ * // related entity. So, e.g. if you are mapping to
+ * // a `FacetValue` relation's `id` property, the value
+ * // would be `facet_value.id`.
* customerLastName: 'customer.lastName',
* },
* };

```

**Candidate message**

> feat(test): Add `customPropertyMap` to allow sorting and filtering by custom fields on related entities

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 28 of 50  ·  id `2793`

**Diff**

```diff
@@ -141,10 +141,10 @@ def generate_example_input(inptype, # type: Any
example = [value]
else:
example = value
- if default:
+ if default is not None:
example = default
elif inptype['type'] == 'enum':
- if default:
+ if default is not None:
example = default
elif 'default' in inptype:
example = inptype['default']
@@ -225,7 +225,7 @@ def load_job_order(args, # type: argparse.Namespace
fetcher_constructor, # Fetcher
overrides_list, # type: List[Dict[Text, Any]]
tool_file_uri # type: Text
- ): # type: (...) -> Tuple[MutableMapping[Text, Any], Text, Loader]
+ ): # type: (...) -> Tuple[Optional[MutableMapping[Text, Any]], Text, Loader]
job_order_object = None
job_order_file = None
@@ -241,23 +241,23 @@ def load_job_order(args, # type: argparse.Namespace
else:
job_order_file = None
- if job_order_object:
+ if job_order_object is not None:
input_basedir = args.basedir if args.basedir else os.getcwd()
- elif job_order_file:
+ elif job_order_file is not None:
input_basedir = args.basedir if args.basedir \
else os.path.abspath(os.path.dirname(job_order_file))
job_order_object, _ = loader.resolve_ref(job_order_file, checklinks=False)
- if job_order_object and "http://commonwl.org/cwltool#overrides" in job_order_object:
+ if job_order_object is not None and "http://commonwl.org/cwltool#overrides" in job_order_object:
ov_uri = file_uri(job_order_file or input_basedir)
overrides_list.extend(
resolve_overrides(job_order_object, ov_uri, tool_file_uri))
del job_order_object["http://commonwl.org/cwltool#overrides"]
- if not job_order_object:
+ if job_order_object is None:
input_basedir = args.basedir if args.basedir else os.getcwd()
- if job_order_object and not isinstance(job_order_object, MutableMapping):
+ if job_order_object is not None and not isinstance(job_order_object, MutableMapping):
_logger.error(
'CWL input object at %s is not formatted correctly, it should be a '
'JSON/YAML dictionay, not %s.\n'
@@ -279,12 +279,11 @@ def init_job_order(job_order_object, # type: Optional[MutableMapping[Text
secret_store=None # type: SecretStore
): # type: (...) -> MutableMapping[Text, Any]
secrets_req, _ = process.get_requirement("http://commonwl.org/cwltool#Secrets")
- if not job_order_object:
+ if job_order_object is None:
namemap = {} # type: Dict[Text, Text]
records = [] # type: List[Text]
toolparser = generate_parser(
argparse.ArgumentParser(prog=args.workflow), process, namemap, records)
- if toolparser:
if args.tool_help:
toolparser.print_help()
exit(0)
@@ -299,7 +298,7 @@ def init_job_order(job_order_object, # type: Optional[MutableMapping[Text
del cmd_line[key]
cmd_line[str(record_name)] = record
- if cmd_line["job_order"]:
+ if 'job_order' in cmd_line and cmd_line["job_order"]:
try:
job_order_object = cast(
MutableMapping, loader.resolve_ref(cmd_line["job_order"])[0])
@@ -320,8 +319,6 @@ def init_job_order(job_order_object, # type: Optional[MutableMapping[Text
if _logger.isEnabledFor(logging.DEBUG):
_logger.debug(u"Parsed job order from command line: %s",
json_dumps(job_order_object, indent=4))
- else:
- job_order_object = None
for inp in process.tool["inputs"]:
if "default" in inp and (
@@ -330,9 +327,9 @@ def init_job_order(job_order_object, # type: Optional[MutableMapping[Text
job_order_object = {}
job_order_object[shortname(inp["id"])] = inp["default"]
- if not job_order_object:
+ if job_order_object is None:
if process.tool["inputs"]:
- if toolparser:
+ if toolparser is not None:
print(u"\nOptions for {} ".format(args.workflow))
toolparser.print_help()
_logger.error("")
@@ -446,7 +443,7 @@ def find_deps(obj, # type: Mapping[Text, Any]
sfs = scandeps(
basedir if basedir else uri, obj, {"$import", "run"},
{"$include", "$schemas", "location"}, loadref, nestdirs=nestdirs)
- if sfs:
+ if sfs is not None:
deps["secondaryFiles"] = sfs
return deps
@@ -496,7 +493,7 @@ def main(argsl=None, # type: List[str]
stdout = cast(TextIO, sys.stdout) # type: ignore
_logger.removeHandler(defaultStreamHandler)
- if logger_handler:
+ if logger_handler is not None:
stderr_handler = logger_handler
else:
stderr_handler = logging.StreamHandler(stderr)
@@ -572,7 +569,7 @@ def main(argsl=None, # type: List[str]
if not args.enable_ga4gh_tool_registry:
del ga4gh_tool_registries[:]
- if custom_schema_callback:
+ if custom_schema_callback is not None:
custom_schema_callback()
elif args.enable_ext:
res = pkg_resources.resource_stream(__name__, 'extensions.yml')
@@ -606,7 +603,7 @@ def main(argsl=None, # type: List[str]
prov_log_handler.setFormatter(ProvLogFormatter())
_logger.addHandler(prov_log_handler)
_logger.debug(u"[provenance] Logging to %s", log_file_io)
- if argsl:
+ if argsl is not None:
# Log cwltool command line options to provenance file
_logger.info("[cwltool] %s %s", sys.argv[0], u" ".join(argsl))
_logger.debug(u"[cwltool] Arguments: %s", args)
@@ -780,7 +777,7 @@ def main(argsl=None, # type: List[str]
logger=_logger)
if out is not None:
- if runtimeContext.research_obj:
+ if runtimeContext.research_obj is not None:
runtimeContext.research_obj.create_job(out, None, True)
def loc_to_path(obj):
@@ -835,7 +832,7 @@ def main(argsl=None, # type: List[str]
research_obj = runtimeContext.research_obj
prov_dependencies = prov_deps(workflowobj, document_loader, uri)
research_obj.generate_snapshot(prov_dependencies)
- if prov_log_handler:
+ if prov_log_handler is not None:
# Stop logging so we won't half-log adding ourself to RO
_logger.debug(u"[provenance] Closing provenance log file %s",
prov_log_handler)

```

**Candidate message**

> feat(additional-checks): Add check for optional default value in `generate_example_input` function

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 29 of 50  ·  id `1104`

**Diff**

```diff
@@ -50,6 +50,18 @@ type Controller struct {
ipset *ipsets.IPSets
protocol string
+ internalIP string
+}
+
+func getNodeInternalIP(node *v1.Node) string {
+ var nodeAddr string
+ for _, addr := range node.Status.Addresses {
+ if addr.Type == v1.NodeInternalIP {
+ nodeAddr = addr.Address
+ break
+ }
+ }
+ return nodeAddr
}
// NewController init a daemon controller
@@ -81,6 +93,7 @@ func NewController(config *Configuration, informerFactory informers.SharedInform
return nil, err
}
controller.protocol = util.CheckProtocol(node.Annotations[util.IpAddressAnnotation])
+ controller.internalIP = getNodeInternalIP(node)
if controller.protocol == kubeovnv1.ProtocolIPv4 {
iptable, err := iptables.NewWithProtocol(iptables.ProtocolIPv4)
@@ -120,7 +133,7 @@ func (c *Controller) enqueueSubnet(obj interface{}) {
c.subnetQueue.Add(key)
}
-func (c *Controller) enqueueUpdateSubnet(old, new interface{}) {
+func (c *Controller) enqueueUpdateSubnet(_, new interface{}) {
var key string
var err error
if key, err = cache.MetaNamespaceKeyFunc(new); err != nil {
@@ -220,7 +233,8 @@ func (c *Controller) reconcileRouters() error {
for _, r := range toAdd {
_, cidr, _ := net.ParseCIDR(r)
gw := net.ParseIP(gateway)
- if err = netlink.RouteReplace(&netlink.Route{Dst: cidr, LinkIndex: nic.Attrs().Index, Scope: netlink.SCOPE_UNIVERSE, Gw: gw}); err != nil {
+ src := net.ParseIP(c.internalIP)
+ if err = netlink.RouteReplace(&netlink.Route{Dst: cidr, LinkIndex: nic.Attrs().Index, Scope: netlink.SCOPE_UNIVERSE, Gw: gw, Src: src}); err != nil {
klog.Errorf("failed to add route %v", err)
}
}

```

**Candidate message**

> feat(adds): `controller#enqueueUpdateSubnet` adds a field `internalIP` and updates the route replacement logic to include the internal IP as the source address

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 30 of 50  ·  id `1274`

**Diff**

```diff
@@ -764,7 +764,7 @@ CompNode _get_device(PyObject*const* args, size_t nargs) {
}
}
if (!valid) {
- mgb_assert(0, "expect at least 1 device");
+ return CompNode::load(get_default_device());
}
Py_XDECREF(tuple);
return cn;

```

**Candidate message**

> feat(add): add support for loading default device via factory method

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 31 of 50  ·  id `2653`

**Diff**

```diff
@@ -50,7 +50,7 @@ pub struct AmbiguityChanges {
/// A deserialized response for the rooms members API call.
///
-/// [GET /_matrix/client/r0/rooms/{roomId}/members](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-r0-rooms-roomid-members)
+/// [`GET /_matrix/client/r0/rooms/{roomId}/members`](https://spec.matrix.org/v1.5/client-server-api/#get_matrixclientv3roomsroomidmembers)
#[derive(Clone, Debug, Default, Deserialize)]
pub struct MembersResponse {
/// The list of members events.

```

**Candidate message**

> feat(doc): document new endpoint in `MembersResponse` struct

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 32 of 50  ·  id `2341`

**Diff**

```diff
@@ -43,13 +43,13 @@ describe Team do
describe '#user?' do
context 'when users in current team includes the parameterized user' do
it 'returns true' do
- expect(team.user? user).to be true
+ expect(team.user?(user)).to be true
end
end
context 'when users in current team does not include the parameterized user' do
it 'returns false' do
- expect(team.user? user2).to be false
+ expect(team.user?(user2)).to be false
end
end
end
@@ -127,7 +127,8 @@ describe Team do
describe '.import_team_members' do
context 'when cannot find a user by name' do
it 'raises an ImportError' do
- expect { team.import_team_members(0, ['TestUser']) }.to raise_error(ImportError, "The user TestUser was not found. <a href='/users/new'>Create</a> this user?")
+ var errorMessage = "The user TestUser was not found. <a href='/users/new'>Create</a> this user?"
+ expect { team.import_team_members(0, ['TestUser']) }.to raise_error(ImportError, errorMessage)
end
end

```

**Candidate message**

> feat(additional-test): Add test for `Team#import_team_members` when user not found

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 33 of 50  ·  id `2672`

**Diff**

```diff
namespace MLAPI.Logging
{
+ /// <summary>
+ /// Log level
+ /// </summary>
public enum LogLevel
{
+ /// <summary>
+ /// Developer logging level, most verbose
+ /// </summary>
Developer,
+ /// <summary>
+ /// Normal logging level, medium verbose
+ /// </summary>
Normal,
+ /// <summary>
+ /// Error logging level, very quiet
+ /// </summary>
Error,
+ /// <summary>
+ /// Nothing logging level, no logging will be done
+ /// </summary>
Nothing
}
+ /// <summary>
+ /// Helper class for logging
+ /// </summary>
public static class LogHelper
{
+ /// <summary>
+ /// Gets the current log level.
+ /// </summary>
+ /// <value>The current log level.</value>
public static LogLevel CurrentLogLevel
{
get
@@ -23,8 +45,20 @@ namespace MLAPI.Logging
}
}
+ /// <summary>
+ /// Logs an info log with the proper MLAPI prefix
+ /// </summary>
+ /// <param name="message">The message to log</param>
public static void LogInfo(string message) => Debug.Log("[MLAPI] " + message);
+ /// <summary>
+ /// Logs a warning log with the proper MLAPI prefix
+ /// </summary>
+ /// <param name="message">The message to log</param>
public static void LogWarning(string message) => Debug.LogWarning("[MLAPI] " + message);
+ /// <summary>
+ /// Logs an error log with the proper MLAPI prefix
+ /// </summary>
+ /// <param name="message">The message to log</param>
public static void LogError(string message) => Debug.LogError("[MLAPI] " + message);
}
}

```

**Candidate message**

> feat(logging): Add `LogLevel` enum with documentation and `LogHelper` class with logging methods

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 34 of 50  ·  id `2787`

**Diff**

```diff
@@ -148,7 +148,7 @@ TEST_P(TraceWriterImplTest, FragmentingPacket) {
// Sets up a scenario in which the SMB is exhausted and TraceWriter fails to get
// a new chunk while fragmenting a packet. Verifies that data is dropped until
// the SMB is freed up and TraceWriter can get a new chunk.
-TEST_P(TraceWriterImplTest, FragmentingPacketWhileBufferExhaused) {
+TEST_P(TraceWriterImplTest, FragmentingPacketWhileBufferExhausted) {
arbiter_.reset(new SharedMemoryArbiterImpl(buf(), buf_size(), page_size(),
&fake_producer_endpoint_,
task_runner_.get()));
@@ -161,7 +161,7 @@ TEST_P(TraceWriterImplTest, FragmentingPacketWhileBufferExhaused) {
auto packet = writer->NewTracePacket();
EXPECT_FALSE(reinterpret_cast<TraceWriterImpl*>(writer.get())
->drop_packets_for_testing());
- EXPECT_EQ(packet->Finalize(), 0);
+ EXPECT_EQ(packet->Finalize(), 0u);
// Grab all the remaining chunks in the SMB in new writers.
std::array<std::unique_ptr<TraceWriter>, kNumPages * 4 - 1> other_writers;
@@ -225,7 +225,7 @@ TEST_P(TraceWriterImplTest, FragmentingPacketWhileBufferExhaused) {
// The first packet in the chunk should have the previous_packet_dropped flag
// set, so shouldn't be empty.
- EXPECT_GT(packet4->Finalize(), 0);
+ EXPECT_GT(packet4->Finalize(), 0u);
// Flushing the writer causes the chunk to be released again.
writer->Flush();

```

**Candidate message**

> test: TEST_P(TraceWriterImplTest, FragmentingPacketWhileBufferExhausted) - fix: EXPECT_EQ -> EXPECT_EQ(u)

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 35 of 50  ·  id `2188`

**Diff**

```diff
@@ -7,7 +7,8 @@ import type {ESLToggleable} from '../../esl-toggleable/core';
export class ESLToggleablePlaceholder extends ESLBaseElement {
public static is = 'esl-toggleable-placeholder';
- public static readonly allowedExtraAttrs: string[] = [];
+ /** List of attributes allowed to copy from origin to this element */
+ public static readonly allowedAttrs: string[] = ['id', 'class'];
public $origin: ESLToggleable | null;
@@ -18,11 +19,6 @@ export class ESLToggleablePlaceholder extends ESLBaseElement {
return $placeholder;
}
- /** List of attributes allowed to copy from origin to this element */
- protected get allowedAttrs(): string[] {
- return ['id', 'class'].concat((this.constructor as typeof ESLToggleablePlaceholder).allowedExtraAttrs);
- }
-
public connectedCallback(): void {
this.copyAttributesFromOrigin();
super.connectedCallback();
@@ -33,7 +29,7 @@ export class ESLToggleablePlaceholder extends ESLBaseElement {
if (!this.$origin) return;
[...this.$origin.attributes]
- .filter((attr) => this.allowedAttrs.includes(attr.nodeName))
+ .filter((attr) => (this.constructor as typeof ESLToggleablePlaceholder).allowedAttrs.includes(attr.nodeName))
.forEach((attr) => {
const {nodeName, nodeValue} = attr;
if (nodeValue) {
```

**Candidate message**

> feat(add-allowed-attrs): Add `allowedAttrs` field to `ESLToggleablePlaceholder` to allow copying of attributes from origin. 📦

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 36 of 50  ·  id `2761`

**Diff**

```diff
@@ -113,6 +113,7 @@ elif [ $SDK_NAME == "cu111" ];then
CUDA_COPY_LIB_LIST="\
${CUDA_LIB_DIR}/libnvrtc.so.11.1:\
+ ${CUDA_LIB_DIR}/libnvrtc-builtins.so.11.1:\
${CUDA_LIB_DIR}/libcublasLt.so.11:\
${CUDA_LIB_DIR}/libcublas.so.11:\
${CUDNN_LIB_DIR}/libcudnn_adv_infer.so.8:\
@@ -145,6 +146,7 @@ elif [ $SDK_NAME == "cu111_cudnn821_tensorRT825" ];then
CUDA_COPY_LIB_LIST="\
${CUDA_LIB_DIR}/libnvrtc.so.11.1:\
+ ${CUDA_LIB_DIR}/libnvrtc-builtins.so.11.1:\
${CUDA_LIB_DIR}/libcublasLt.so.11:\
${CUDA_LIB_DIR}/libcublas.so.11:\
${CUDNN_LIB_DIR}/libcudnn_adv_infer.so.8:\
@@ -170,6 +172,7 @@ elif [ $SDK_NAME == "cu112" ];then
BUILD_GCC8="ON"
CUDA_COPY_LIB_LIST="\
${CUDA_LIB_DIR}/libnvrtc.so.11.2:\
+ ${CUDA_LIB_DIR}/libnvrtc-builtins.so.11.2:\
${CUDA_LIB_DIR}/libcublasLt.so.11:\
${CUDA_LIB_DIR}/libcublas.so.11:\
${CUDNN_LIB_DIR}/libcudnn_adv_infer.so.8:\

```

**Candidate message**

> feat(cudnn): add `libnvrtc-builtins.so` to `CUDA_COPY_LIB_LIST` for `cu111_cudnn821_tensorRT825` and `cu112`

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 37 of 50  ·  id `560`

**Diff**

```diff
-# rubocop:disable InstanceVariable, DepartmentName
+# rubocop:disable RSpec/InstanceVariable
require 'spec_helper_min'
require 'support/helpers'
@@ -1877,4 +1877,4 @@ describe Carto::Api::ApiKeysController do
end
end
-# rubocop:enable InstanceVariable, DepartmentName
+# rubocop:enable RSpec/InstanceVariable

```

**Candidate message**

> feat(test): Enable RSpec instance variable disabling in test files

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 38 of 50  ·  id `244`

**Diff**

```diff
-open class PosterPlugin: UIContainerPlugin {
+open class PosterPlugin: OverlayPlugin {
var poster = UIImageView(frame: CGRect.zero)
fileprivate var playButton = UIButton(frame: CGRect.zero)
- private var isChromeless: Bool { container?.options.bool(kChromeless) ?? false }
+ private var isChromeless: Bool { core?.options.bool(kChromeless) ?? false }
open override class var name: String {
return "poster"
@@ -14,17 +14,17 @@ open class PosterPlugin: UIContainerPlugin {
}
open override func render() {
- guard let container = container else { return }
+ guard let core = core else { return }
if isChromeless {
view.isHidden = true
}
- if let urlString = container.options[kPosterUrl] as? String {
+ if let urlString = core.options[kPosterUrl] as? String {
setPosterImage(with: urlString)
} else {
view.isHidden = true
- container.mediaControlEnabled = false
+ core.activeContainer?.mediaControlEnabled = false
}
configurePlayButton()
@@ -49,12 +49,12 @@ open class PosterPlugin: UIContainerPlugin {
}
@objc func playTouched() {
- playback?.seek(0)
- playback?.play()
+ activePlayback?.seek(0)
+ activePlayback?.play()
}
fileprivate func configureViews() {
- container?.view.addMatchingConstraints(view)
+ core?.overlayView.addMatchingConstraints(view)
view.addSubviewMatchingConstraints(poster)
view.addSubview(playButton)
@@ -68,30 +68,24 @@ open class PosterPlugin: UIContainerPlugin {
view.addConstraint(yCenterConstraint)
}
- override open func bindEvents() {
- guard !isChromeless else { return }
- bindContainerEvents()
- bindPlaybackEvents()
- }
-
- private func bindPlaybackEvents() {
- if let playback = playback {
- listenTo(playback, eventName: Event.playing.rawValue) { [weak self] _ in self?.playbackStarted() }
- listenTo(playback, eventName: Event.stalling.rawValue) { [weak self] _ in self?.playbackStalled() }
- }
- }
+ override open func bindEvents() {}
- private func bindContainerEvents() {
- guard let container = container else { return }
+ override open func onDidChangeActiveContainer() {
+ guard let container = activeContainer else { return }
listenTo(container, eventName: Event.requestPosterUpdate.rawValue) { [weak self] info in self?.updatePoster(info) }
listenTo(container, eventName: Event.didUpdateOptions.rawValue) { [weak self] _ in self?.updatePoster(container.options) }
}
override open func onDidChangePlayback() {
- if isNoOpPlayback {
+ if let playback = activePlayback {
+ listenTo(playback, eventName: Event.playing.rawValue) { [weak self] _ in self?.playbackStarted() }
+ listenTo(playback, eventName: Event.stalling.rawValue) { [weak self] _ in self?.playbackStalled() }
+
+ if playback is NoOpPlayback {
view.isHidden = true
}
}
+ }
fileprivate func playbackStalled() {
playButton.isHidden = true

```

**Candidate message**

> feat(overlay): Update `PosterPlugin` to use `core` instead of `container` for `isChromeless` and improve event handling logic. 🎬

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: fail
- specificity: pass

---

## 39 of 50  ·  id `2114`

**Diff**

```diff
@@ -85,15 +85,19 @@ func newPerfEventRing(cpu int, opts PerfReaderOptions) (*perfEventRing, error) {
// documentation, since a byte is smaller than sampledPerfEvent.
meta := (*perfEventMeta)(unsafe.Pointer(&mmap[0]))
- return &perfEventRing{
+ ring := &perfEventRing{
fd: fd,
meta: meta,
mmap: mmap,
ring: mmap[meta.dataOffset : meta.dataOffset+meta.dataSize],
- }, nil
+ }
+ runtime.SetFinalizer(ring, (*perfEventRing).Close)
+
+ return ring, nil
}
func (ring *perfEventRing) Close() {
+ runtime.SetFinalizer(ring, nil)
unix.Close(ring.fd)
unix.Munmap(ring.mmap)
}

```

**Candidate message**

> feat(test): Add finalizer to perfEventRing to ensure proper cleanup

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 40 of 50  ·  id `2677`

**Diff**

```diff
@@ -137,13 +137,12 @@ public final class Net {
public native static int getTcpNoDelay(long fd);
/**
- *
* This method reads 1 byte (or none if the socket is non blocking and there is no data).
* If there is no error (EOF ?) then it returns false
* If there is an error (EOF ?) then it returns true
*
- * @param fd
- * @return
+ * @param fd network file descriptor
+ * @return check the description
*/
public static native boolean isDead(long fd);

```

**Candidate message**

> feat(adds-method): add method `isDead` to check if a network file descriptor is dead. 📦

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 41 of 50  ·  id `69`

**Diff**

```diff
@@ -83,7 +83,7 @@ function configureAuthForServer(server) {
const { id } = decodeOpaqueId(req.params.userId);
// Ask IDP to log us out
- fetch(`${config.OAUTH2_IDP_HOST_URL}logout?userId=${id}`)
+ fetch(`${config.OAUTH2_IDP_HOST_URL}logout-user?userId=${id}`)
.then((logoutResponse) => {
if (logoutResponse.status >= 400) {
const message = `Error from OAUTH2_IDP_HOST_URL logout endpoint: ${logoutResponse.status}. Check the HOST server settings`;

```

**Candidate message**

> feat(auth): Update OAUTH2_IDP_HOST_URL endpoint to use `logout-user` instead of `logout` and add error handling

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 42 of 50  ·  id `644`

**Diff**

```diff
#include "google/cloud/testing_util/assert_ok.h"
#include "google/cloud/testing_util/chrono_literals.h"
#include "absl/memory/memory.h"
-#include "google/protobuf/util/time_util.h"
+#include <google/protobuf/util/time_util.h>
#include <gmock/gmock.h>
#include <string>
#include <vector>

```

**Candidate message**

> feat(additional-header): add include for Google Protobuf util header

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 43 of 50  ·  id `2773`

**Diff**

```diff
@@ -177,7 +177,7 @@ namespace Cicada {
}
if (mFiler == nullptr) {
- mFiler = std::unique_ptr<ffmpegAudioFilter>(new ffmpegAudioFilter(mInfo, mInfo));
+ mFiler = std::unique_ptr<ffmpegAudioFilter>(new ffmpegAudioFilter(mInfo, mInfo, true));
mFiler->init();
}

```

**Candidate message**

> feat(test): add flag to initialize ffmpegAudioFilter with debug mode

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 44 of 50  ·  id `2809`

**Diff**

```diff
#include <climits> // For UINT_MAX.
#include <iostream>
#include <string>
-#include <queue>
#include <vector>
namespace elastix
@@ -151,8 +150,6 @@ ELASTIX::RegisterImages(
typedef ArgumentMapType::value_type ArgumentMapEntryType;
typedef std::pair< std::string, std::string > ArgPairType;
- typedef std::queue< ArgPairType > ParameterFileListType;
- typedef ParameterFileListType::value_type ParameterFileListEntryType;
// Clear output transform parameters
this->m_TransformParametersList.clear();
@@ -168,7 +165,6 @@ ELASTIX::RegisterImages(
FlatDirectionCosinesType fixedImageOriginalDirection;
int returndummy = 0;
ArgumentMapType argMap;
- ParameterFileListType parameterFileList;
std::string outFolder = "";
std::string logFileName = "";
std::string key;

```

**Candidate message**

> feat(add-parameter-file-list): Add parameter file list type with queue structure

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 45 of 50  ·  id `640`

**Diff**

```diff
import * as React from 'react';
+import * as PropTypes from 'prop-types';
import {Box, BoxProps} from '@twilio-paste/box';
-import {Space} from '@twilio-paste/style-props';
+import {Space, isSpaceTokenProp} from '@twilio-paste/style-props';
export interface MediaObjectProps extends Pick<BoxProps, 'as' | 'marginTop' | 'marginBottom'> {
verticalAlign?: 'center' | 'top';
@@ -25,12 +26,19 @@ const MediaObject: React.FC<MediaObjectProps> = ({
</Box>
);
};
+
MediaObject.displayName = 'MediaObject';
+if (process.env.NODE_ENV === 'development') {
+ MediaObject.propTypes = {
+ verticalAlign: PropTypes.oneOf(['center', 'top']),
+ };
+}
export interface MediaFigureProps extends Pick<BoxProps, 'as'> {
align?: 'start' | 'end';
spacing?: Space;
}
+
const MediaFigure: React.FC<MediaFigureProps> = ({as = 'span', children, align, spacing}) => {
return (
<Box
@@ -44,13 +52,21 @@ const MediaFigure: React.FC<MediaFigureProps> = ({as = 'span', children, align,
</Box>
);
};
+
MediaFigure.displayName = 'MediaFigure';
MediaFigure.defaultProps = {
align: 'start',
spacing: 'space0',
};
+if (process.env.NODE_ENV === 'development') {
+ MediaFigure.propTypes = {
+ align: PropTypes.oneOf(['start', 'end']),
+ spacing: isSpaceTokenProp,
+ };
+}
export type MediaBodyProps = Pick<BoxProps, 'as'>;
+
const MediaBody: React.FC<MediaBodyProps> = ({as = 'span', children}) => {
return (
<Box as={as} flex={1}>
@@ -58,6 +74,7 @@ const MediaBody: React.FC<MediaBodyProps> = ({as = 'span', children}) => {
</Box>
);
};
+
MediaBody.displayName = 'MediaBody';
export {MediaObject, MediaFigure, MediaBody};

```

**Candidate message**

> feat(media-component): Added `@twilio-paste/style-props` dependency and added type definitions for `MediaFigure` and `MediaBody`. 📦

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: fail
- completeness: pass
- specificity: pass

---

## 46 of 50  ·  id `2315`

**Diff**

```diff
@@ -52,8 +52,6 @@ type AppModuleBasic interface {
RegisterLegacyAminoCodec(*codec.LegacyAmino)
RegisterInterfaces(codectypes.InterfaceRegistry)
- HasGenesisBasics
-
// client functionality
RegisterGRPCGatewayRoutes(client.Context, *runtime.ServeMux)
GetTxCmd() *cobra.Command
@@ -103,7 +101,9 @@ func (bm BasicManager) RegisterInterfaces(registry codectypes.InterfaceRegistry)
func (bm BasicManager) DefaultGenesis(cdc codec.JSONCodec) map[string]json.RawMessage {
genesis := make(map[string]json.RawMessage)
for _, b := range bm {
- genesis[b.Name()] = b.DefaultGenesis(cdc)
+ if mod, ok := b.(HasGenesisBasics); ok {
+ genesis[b.Name()] = mod.DefaultGenesis(cdc)
+ }
}
return genesis
@@ -112,10 +112,12 @@ func (bm BasicManager) DefaultGenesis(cdc codec.JSONCodec) map[string]json.RawMe
// ValidateGenesis performs genesis state validation for all modules
func (bm BasicManager) ValidateGenesis(cdc codec.JSONCodec, txEncCfg client.TxEncodingConfig, genesis map[string]json.RawMessage) error {
for _, b := range bm {
- if err := b.ValidateGenesis(cdc, txEncCfg, genesis[b.Name()]); err != nil {
+ if mod, ok := b.(HasGenesisBasics); ok {
+ if err := mod.ValidateGenesis(cdc, txEncCfg, genesis[b.Name()]); err != nil {
return err
}
}
+ }
return nil
}

```

**Candidate message**

> feat(validator): Add support for `HasGenesisBasics` validation in validator module

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 47 of 50  ·  id `2107`

**Diff**

```diff
+import { equiv } from "@thi.ng/api/equiv";
import * as isa from "@thi.ng/checks/is-array";
import * as iss from "@thi.ng/checks/is-string";
import * as diff from "@thi.ng/diff";
@@ -38,7 +39,7 @@ export function diffElement(root: Element, prev: any, curr: any) {
}
function _diffElement(parent: Element, prev: any, curr: any, child: number) {
- const delta = diffArray(prev, curr);
+ const delta = diffArray(prev, curr, equiv, true);
if (delta.distance === 0) {
return;
}

```

**Candidate message**

> feat(additional-logic): add support for equiv check in diffArray

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 48 of 50  ·  id `166`

**Diff**

```diff
package com.chesire.malime.flow
+import android.content.Intent
import android.os.Bundle
+import com.chesire.malime.flow.login.LoginActivity
import dagger.android.DaggerActivity
class LaunchActivity : DaggerActivity() {
override fun onCreate(savedInstanceState: Bundle?) {
super.onCreate(savedInstanceState)
+ startActivity(Intent(this, LoginActivity::class.java))
+ finish()
// if not performed oob, go to oob flow
// if logged in, go to the logged in flow

```

**Candidate message**

> feat(additional-logic): Add logic to launch the login flow when the app is first opened. 📦

**Ratings** (pass / fail):
- type_correctness: pass
- faithfulness: pass
- completeness: pass
- specificity: pass

---

## 49 of 50  ·  id `2103`

**Diff**

```diff
@@ -29,7 +29,6 @@ impl<'a> PostOrderIterator<'a> {
opts: TreeOptions,
) -> Self {
full_path.clear();
- block_buffer.clear();
PostOrderIterator {
full_path,
@@ -79,21 +78,22 @@ impl<'a> PostOrderIterator<'a> {
// FIXME: we shouldn't be creating too large structures (bitswap block size limit!)
// FIXME: changing this to autosharding is going to take some thinking
- buffer.clear();
let cap = buffer.capacity();
if let Some(additional) = size.checked_sub(cap) {
buffer.reserve(additional);
}
- // TODO: this could be done more integelligently; for example, we could just zero extend
- // on reserving, then just truncate or somehow carry around the real length of the buffer
- // to avoid truncating and zero extending.
- buffer.extend(std::iter::repeat(0).take(size));
+ if let Some(needed_zeroes) = size.checked_sub(buffer.len()) {
+ buffer.extend(std::iter::repeat(0).take(needed_zeroes));
+ }
let mut writer = Writer::new(BytesWriter::new(&mut buffer[..]));
flat.write_message(&mut writer)
.expect("unsure how this could fail");
+
+ buffer.truncate(size);
+
let mh = multihash::wrap(multihash::Code::Sha2_256, &Sha256::digest(&buffer));
let cid = Cid::new_v0(mh).expect("sha2_256 is the correct multihash for cidv0");
@@ -177,9 +177,7 @@ impl<'a> PostOrderIterator<'a> {
return None;
}
- // render unixfs, maybe return it?
let buffer = &mut self.block_buffer;
- buffer.clear();
let leaf = match Self::render_directory(&collected, buffer) {
Ok(leaf) => leaf,

```

**Candidate message**

> feat(add): Add support for rendering directory contents in PostOrderIterator

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: fail
- completeness: fail
- specificity: pass

---

## 50 of 50  ·  id `2811`

**Diff**

```diff
@@ -107,22 +107,20 @@ BSINT32 BoatWalletCreate( BoatProtocolType protocol_type, const BCHAR *wallet_na
BUINT8 hashLenDummy;
#endif
- boatwalletStore_ptr = BoatMalloc(wallet_config_size + sizeof(BoatWalletPriKeyCtx));
- if( NULL == boatwalletStore_ptr )
+ /* Check wallet configuration */
+ if( (wallet_name_str == NULL) && (wallet_config_ptr == NULL) )
{
- BoatLog(BOAT_LOG_NORMAL, "Failed to allocate memory.");
+ BoatLog(BOAT_LOG_NORMAL, "Invalid wallet configuration.");
return BOAT_ERROR;
}
- memset(boatwalletStore_ptr, 0, wallet_config_size + sizeof(BoatWalletPriKeyCtx));
- /* Check wallet configuration */
- if( (wallet_name_str == NULL) && (wallet_config_ptr == NULL) )
+ boatwalletStore_ptr = BoatMalloc(wallet_config_size + sizeof(BoatWalletPriKeyCtx));
+ if( NULL == boatwalletStore_ptr )
{
- BoatLog(BOAT_LOG_NORMAL, "Invalid wallet configuration.");
+ BoatLog(BOAT_LOG_NORMAL, "Failed to allocate memory.");
return BOAT_ERROR;
}
- /* Check the parameter of config is valid or not */
- //! @todo Check the parameter of config is valid or not
+ memset(boatwalletStore_ptr, 0, wallet_config_size + sizeof(BoatWalletPriKeyCtx));
/* For Multi-Thread Support: ObtainMutex Here */
for( i = 0; i < BOAT_MAX_WALLET_NUM; i++ )
@@ -143,7 +141,6 @@ BSINT32 BoatWalletCreate( BoatProtocolType protocol_type, const BCHAR *wallet_na
/* Check protocol type */
g_boat_iot_sdk_context.wallet_list[i].protocol_type = protocol_type;
-
switch(protocol_type)
{
#if PROTOCOL_USE_ETHEREUM == 1

```

**Candidate message**

> feat(add-validation-check): Add validation check for wallet configuration before allocating memory

**Ratings** (pass / fail):
- type_correctness: fail
- faithfulness: pass
- completeness: pass
- specificity: pass
