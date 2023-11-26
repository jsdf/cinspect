#include <iostream>
#include <clang-c/Index.h> // This is libclang.
using namespace std;

int main()
{
    CXIndex index = clang_createIndex(0, 0);
    CXTranslationUnit unit = clang_parseTranslationUnit(
        index,
        "test/hello.c", nullptr, 0,
        nullptr, 0,
        CXTranslationUnit_None);
    if (unit == nullptr)
    {
        cerr << "Unable to parse translation unit. Quitting." << endl;
        exit(-1);
    }
    else
    {
        cout << "Parsed translation unit." << endl;
        // print any parsing diagnostics
        unsigned int numDiagnostics = clang_getNumDiagnostics(unit);
        for (unsigned int i = 0; i < numDiagnostics; ++i)
        {
            CXDiagnostic diag = clang_getDiagnostic(unit, i);
            CXString string = clang_formatDiagnostic(diag, clang_defaultDiagnosticDisplayOptions());
            cerr << clang_getCString(string) << endl;
            clang_disposeString(string);
        }

        // print out the AST for the translation unit
        CXCursor cursor = clang_getTranslationUnitCursor(unit);
        clang_visitChildren(
            cursor,
            [](CXCursor c, CXCursor parent, CXClientData client_data) -> CXChildVisitResult
            {
                CXSourceLocation location = clang_getCursorLocation(c);
                CXString filename;
                unsigned int line, column, offset;
                clang_getPresumedLocation(location, &filename, &line, &column);
                clang_getExpansionLocation(location, nullptr, &offset, nullptr, nullptr);
                cout << clang_getCString(filename) << ":" << line << ":" << column << ":" << offset << endl;
                clang_disposeString(filename);
                return CXChildVisit_Recurse;
            },
            nullptr);
    }

    clang_disposeTranslationUnit(unit);
    clang_disposeIndex(index);
}