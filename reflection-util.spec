Name:		reflection-util
Version:	1.0.6
Release:	1
Summary:	Conversions between Java type name forms
Group:		Development/Java
License:	MIT
URL:		https://github.com/plume-lib/reflection-util
# Tag v1.0.6 with the Gradle wrapper jar removed.
Source0:	https://github.com/plume-lib/reflection-util/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(org.checkerframework:checker-qual) = 3.41.0-eisop1
Requires:	mvn(org.checkerframework:checker-qual) = 3.41.0-eisop1

%description
org.plumelib:reflection-util converts among string forms of Java types.
Signatures refers to eisop checker-qual annotations such as
BinaryNameWithoutPackage. Those annotations are not in checker-qual 4.4.0,
so this package compiles against the versioned eisop jar.

%prep
%autosetup -n %{name}-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
find src/main/java -name '*.java' ! -name 'module-info.java' > sources.list
test "$(wc -l < sources.list)" -eq 4
mkdir -p classes
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
	-cp %{_javadir}/checker-qual-3.41.0-eisop1.jar \
	-d classes @sources.list
jar cf reflection-util.jar -C classes .
jar i reflection-util.jar
jar tf reflection-util.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
javap -verbose -cp reflection-util.jar org.plumelib.reflection.Signatures | grep -F -q 'major version: 52'

cat > reflection-util.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.plumelib</groupId>
  <artifactId>reflection-util</artifactId>
  <version>1.0.6</version>
  <name>Reflection-util</name>
  <description>Convert among string representations of Java types.</description>
  <licenses>
    <license>
      <name>MIT License</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>checker-qual</artifactId>
      <version>3.41.0-eisop1</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact reflection-util.pom:reflection-util.jar \
	--file-name reflection-util \
	--filelist .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check
cat > check/Smoke.java << 'END'
import org.plumelib.reflection.Signatures;
public class Smoke {
	public static void main(String[] args) {
		String d = Signatures.binaryNameToFieldDescriptor("java.lang.String");
		if (!"Ljava/lang/String;".equals(d)) {
			throw new RuntimeException(d);
		}
		System.out.println("refl_ok " + d);
	}
}
END
QUAL=%{_javadir}/checker-qual-3.41.0-eisop1.jar
JAR=%{buildroot}%{_javadir}/reflection-util.jar
test -f "$QUAL"
test -f "$JAR"
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none -cp "$JAR:$QUAL" -d check check/Smoke.java
java -cp "check:$JAR:$QUAL" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'refl_ok Ljava/lang/String;' check/out.txt

%files -f .mfiles
%doc LICENSE README.md
