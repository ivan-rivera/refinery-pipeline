# Fix Linting Errors

When a linting or pre-commit error occurs:
1. **Identify**: Run the project's lint command to get a full list of errors.
2. **Analyze**: Categorize errors into "auto-fixable" and "manual."
3. **Execute**:
   - Use the appropriate CLI fix command first.
   - For remaining errors, modify the code directly to adhere to the project's style guide.
4. **Verify**: Run the lint command again to ensure 0 errors remain before handing control back to the commit flow.
