// Copyright (c) 2012 by István Váradi

// This file is part of JSProg, a joystick programming utility

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

//------------------------------------------------------------------------------

#include "Profile.h"

#include "Key.h"
#include "Axis.h"
#include "Log.h"

#include <cstring>
#include <cstdlib>
#include <climits>
#include <cerrno>

#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/SAX2.h>
#include <libxml/xmlstring.h>

//------------------------------------------------------------------------------

using std::string;

//------------------------------------------------------------------------------

namespace {

//------------------------------------------------------------------------------

void logSAX(void* ctxt, int level, const char* msg, va_list& ap)
{
    const char* type = (level==Log::LEVEL_ERROR) ? "error" : "warning";
    xmlParserCtxt* context = reinterpret_cast<xmlParserCtxt*>(ctxt);
    if (context->input!=0) {
        const char* filename = context->input->filename;
        if (filename==0) filename = "<profile>";
        Log::log(level, true, "%s:%d:%d: %s: ", filename, context->input->line,
                 context->input->col, type);
    } else {
        Log::log(level, true, "%s: ", type);
    }
    Log::cont(msg, ap);
}

//------------------------------------------------------------------------------

void logSAXError(void* ctxt, const char* msg, ...)
{
    va_list ap;
    va_start(ap, msg);
    logSAX(ctxt, Log::LEVEL_ERROR, msg, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

void logSAXWarning(void* ctxt, const char* msg, ...)
{
    va_list ap;
    va_start(ap, msg);
    logSAX(ctxt, Log::LEVEL_WARNING, msg, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

} /* anonymous namespace */

//------------------------------------------------------------------------------

xmlDoc* Profile::parseFile(const char* filename)
{
    FILE* f = fopen(filename, "rt");
    if (f==0) {
        Log::error("Profile::parseFile: failed to open file '%s'\n", filename);
        return 0;
    }

    xmlSAXHandler saxHandler;
    memset(&saxHandler, 0, sizeof(saxHandler));
    xmlSAX2InitDefaultSAXHandler(&saxHandler, 1);
    saxHandler.warning= &logSAXWarning;
    saxHandler.error= &logSAXError;
    saxHandler.fatalError= &logSAXError;

    xmlParserCtxt* ctxt = 0;

    char buf[1024];
    while(true) {
        int res = fread(buf, 1, sizeof(buf), f);
        if (res<0) {
            Log::error("Profile::parseFile: failed to read '%s'\n", filename);
            fclose(f);
            if (ctxt!=0) xmlFreeParserCtxt(ctxt);
            return 0;
        } else if (res==0) {
            break;
        }
        if (ctxt==0) {
            ctxt = xmlCreatePushParserCtxt(&saxHandler, 0, buf, res, filename);
            if (ctxt==0) {
                Log::error("Profile::parseFile: failed to create parser context for '%s'\n", filename);
                fclose(f);
                return 0;
            }
        } else {
            xmlParseChunk(ctxt, buf, res, 0);
        }
    }

    fclose(f);

    if (ctxt==0) {
        Log::error("Profile::parseFile: failed to read anything from '%s'\n", filename);
        return 0;
    }

    xmlParseChunk(ctxt, buf, 0, 1);

    bool wellFormed = ctxt->wellFormed;
    xmlDoc* doc = ctxt->myDoc;

    xmlFreeParserCtxt(ctxt);

    if (wellFormed) {
        xmlNode* rootNode = xmlDocGetRootElement(doc);
        if (rootNode==0 || strcmp(reinterpret_cast<const char*>(rootNode->name),
                                  "jsprogProfile")!=0)
        {
            Log::debug("Profile::parseFile: invalid root node in %s\n", filename);
            xmlFreeDoc(doc);
            return 0;
        }
        return doc;
    } else {
        Log::error("Profile::parseFile: failed to parse '%s'\n", filename);
        xmlFreeDoc(doc);
        return 0;
    }
}

//------------------------------------------------------------------------------

xmlDoc* Profile::parseString(const char* s)
{
    xmlSAXHandler saxHandler;
    memset(&saxHandler, 0, sizeof(saxHandler));
    xmlSAX2InitDefaultSAXHandler(&saxHandler, 1);
    saxHandler.warning= &logSAXWarning;
    saxHandler.error= &logSAXError;
    saxHandler.fatalError= &logSAXError;

    xmlParserCtxt* ctxt =
        xmlCreatePushParserCtxt(&saxHandler, 0, s, strlen(s), "<profile>");
    if (ctxt==0) {
        Log::error("Profile::parseString: failed to create parser context\n");
        return 0;
    }
    xmlParseChunk(ctxt, s, 0, 1);

    bool wellFormed = ctxt->wellFormed;
    xmlDoc* doc = ctxt->myDoc;

    xmlFreeParserCtxt(ctxt);

    if (wellFormed) {
        xmlNode* rootNode = xmlDocGetRootElement(doc);
        if (rootNode==0 || strcmp(reinterpret_cast<const char*>(rootNode->name),
                                  "jsprogProfile")!=0)
        {
            Log::debug("Profile::parseString: invalid root node\n");
            xmlFreeDoc(doc);
            return 0;
        }
        return doc;
    } else {
        Log::error("Profile::parseString: failed to parse profile\n");
        xmlFreeDoc(doc);
        return 0;
    }
}

//------------------------------------------------------------------------------

bool Profile::isNodeNamed(xmlNode* node, void* data)
{
    if (node==0 || node->type!=XML_ELEMENT_NODE) {
        return false;
    } else {
        return strcmp(reinterpret_cast<const char*>(node->name),
                      reinterpret_cast<const char*>(data))==0;
    }
}

//------------------------------------------------------------------------------

bool Profile::isNodeControl(xmlNode* node, void* /*data*/)
{
    if (node==0 || node->type!=XML_ELEMENT_NODE) {
        return false;
    } else {
        const char* name = reinterpret_cast<const char*>(node->name);
        return strcmp(name, "key")==0 || strcmp(name, "axis")==0;
    }
}

//------------------------------------------------------------------------------

xmlNode* Profile::findNode(xmlNode* node,
                           nodePredicate_t predicate, void* data)
{
    for(; node!=0; node=node->next) {
        if (predicate(node, data)) return node;
    }
    return 0;
}

//------------------------------------------------------------------------------

xmlNode* Profile::findNode(xmlNode* node, const char* name)
{
    return findNode(node, &isNodeNamed, const_cast<char*>(name));
}

//------------------------------------------------------------------------------

bool Profile::extractText(std::string& text, xmlNode* node)
{
    if (node==0) return false;

    text.clear();
    for(; node!=0; node=node->next) {
        if ((node->type==XML_CDATA_SECTION_NODE || node->type==XML_TEXT_NODE) &&
            node->content!=0)
        {
            text += reinterpret_cast<const char*>(node->content);
        }
    }
    return !text.empty();
}

//------------------------------------------------------------------------------

bool Profile::extractAttr(std::string& text, xmlNode* node,
                          const char* name)
{
    if (node->properties==0) return false;

    for(xmlAttr* attr = node->properties; attr!=0; attr=attr->next) {
        if (strcmp(reinterpret_cast<const char*>(attr->name), name)==0) {
            return extractText(text, attr->children);
        }
    }
    return false;
}

//------------------------------------------------------------------------------

Profile::Profile(const char* fileNameOrString, bool isFileName) :
    doc(isFileName ? parseFile(fileNameOrString) :
        parseString(fileNameOrString)),
    nextControl(0)
{
    if (doc!=0) {
        resetControls();
    }
}

//------------------------------------------------------------------------------

Profile::~Profile()
{
    if (doc!=0) xmlFreeDoc(doc);
}

//------------------------------------------------------------------------------

bool Profile::getPrologue(string& luaCode) const
{
    xmlNode* rootNode = xmlDocGetRootElement(doc);
    xmlNode* prologueNode = findNode(rootNode->children, "prologue");
    return (prologueNode==0) ?
        false : extractText(luaCode, prologueNode->children);
}


//------------------------------------------------------------------------------

void Profile::resetControls() const
{
    nextControl = xmlDocGetRootElement(doc)->children;
}

//------------------------------------------------------------------------------

bool Profile::getNextControl(Control::type_t& type, int& code, string& luaCode) const
{
    while(true) {
        xmlNode* controlNode = findNode(nextControl, &isNodeControl, 0);
        if (controlNode==0) return false;

        nextControl = controlNode->next;

        const char* nodeName = reinterpret_cast<const char*>(controlNode->name);
        type = (strcmp(nodeName, "key")==0) ? Control::KEY : Control::AXIS;
        code = -1;

        std::string value;
        if (extractAttr(value, controlNode, "code")) {
            const char* v = value.c_str();
            char* endptr = 0;
            bool isHex = value.length()>2 && v[0]=='0' && v[1]=='x';
            unsigned long x = strtoul(v + (isHex ? 2 : 0), &endptr,
                                      isHex ? 16 : 10);
            if ((x!=ULONG_MAX || errno!=ERANGE) && *endptr=='\0') {
                code = static_cast<int>(x);
            }
        }

        if (code<0 && extractAttr(value, controlNode, "name")) {
            code = (type==Control::KEY) ?
                Key::fromString(value) : Axis::fromString(value);
        }

        if (code<0) {
            Log::warning("Profile::getNextControl: control node of type %s on line %d has no valid code or name attribute, skipping\n",
                         (type==Control::KEY) ? "key" : "axis",
                         controlNode->line);
            continue;
        }

        if (!extractText(luaCode, controlNode->children)) {
            Log::warning("Profile::getNextControl: control node of type %s on line %d has no valid Lua code, skipping\n",
                         (type==Control::KEY) ? "key" : "axis",
                         controlNode->line);
            continue;
        }

        return true;
    }

    return false;
}

//------------------------------------------------------------------------------

bool Profile::getEpilogue(string& luaCode) const
{
    xmlNode* rootNode = xmlDocGetRootElement(doc);
    xmlNode* epilogueNode = findNode(rootNode->children, "epilogue");
    return (epilogueNode==0) ?
        false : extractText(luaCode, epilogueNode->children);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
